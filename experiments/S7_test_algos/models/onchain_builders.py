"""
onchain_builders.py

Standardized 8-step model pipeline:

1) Instantiate dataclasses with defaults
2) Load YAML config
3) Load raw data
4) Pre-process (pivot, etc.)
5) Run score calculator
6) Package into 'analysis'
7) Serialize final results
8) Return 'analysis'
"""

from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
import yaml


@dataclass
class DataSnapshot:
    data_dir: str
    projects_file: str
    metrics_file: str

@dataclass
class SimulationConfig:
    periods: Dict[str, str]
    chains: Dict[str, float]    
    metrics: Dict[str, float]
    metric_variants: Dict[str, float]
    aggregation: Dict[str, str]

class OnchainBuildersCalculator:
    """
    Encapsulates logic for pivoting and computing metric-based scores.
    Produces an 'analysis' dict of all intermediate DataFrames.
    """

    def __init__(self, config: SimulationConfig):
        self.config = config

    def run_analysis(self, df_data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Main pipeline producing an 'analysis' dictionary with all intermediate steps.
        """
        analysis = {}

        # Step 1: Pivot raw data
        analysis["pivoted_raw_metrics_by_chain"] = self._filter_and_pivot_raw_metrics_by_chain(df_data)

        # Step 2: Sum & weight
        analysis["pivoted_raw_metrics_weighted_by_chain"] = self._sum_and_weight_raw_metrics_by_chain(
            analysis["pivoted_raw_metrics_by_chain"]
        )

        # Step 3: Calculate metric variants
        analysis["pivoted_metric_variants"] = self._calculate_metric_variants(
            analysis["pivoted_raw_metrics_weighted_by_chain"]
        )

        # Step 4: Normalize
        analysis["normalized_metric_variants"] = self._normalize_metric_variants(
            analysis["pivoted_metric_variants"]
        )

        # Step 5: Apply weights
        analysis["weighted_metric_variants"] = self._apply_weights_to_metric_variants(
            analysis["normalized_metric_variants"]
        )

        # Step 6: Aggregate final scores
        analysis["aggregated_project_scores"] = self._aggregate_metric_variants(
            analysis["weighted_metric_variants"]
        )

        # Step 7: Final weighting and flattening
        analysis["final_results"] = self._prepare_final_results(analysis)

        return analysis

    # --------------------------------------------------------------------
    # Internal methods
    # --------------------------------------------------------------------

    def _filter_and_pivot_raw_metrics_by_chain(self, df: pd.DataFrame) -> pd.DataFrame:
        metrics_list = list(self.config.metrics.keys())
        periods_list = list(self.config.periods.keys())
        return (
            df.query("metric_name in @metrics_list and measurement_period in @periods_list")
            .pivot_table(
                index=['project_id', 'project_name', 'display_name', 'chain'],
                columns=['measurement_period', 'metric_name'],
                values='amount',
                aggfunc='sum',
                fill_value=0
            )
        )

    def _sum_and_weight_raw_metrics_by_chain(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sum and weight raw metrics by chain weighting."""
        chain_weights = pd.Series(self.config.chains)
        weighted_df = (
            df.mul(df.index.get_level_values('chain').map(chain_weights).fillna(1.0), axis=0)
              .groupby(['project_id', 'project_name', 'display_name'])
              .sum()
        )
        return weighted_df

    def _calculate_metric_variants(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute Adoption, Growth, Retention from current vs. previous period."""
        current_period = next(k for k, v in self.config.periods.items() if v == 'current')
        previous_period = next(k for k, v in self.config.periods.items() if v == 'previous')

        variant_scores = {}
        for metric in self.config.metrics.keys():
            current_vals = df[(current_period, metric)].fillna(0)
            prev_vals = df[(previous_period, metric)].fillna(0)

            variant_scores[(metric, 'Adoption')] = current_vals
            variant_scores[(metric, 'Growth')] = (current_vals - prev_vals).clip(lower=0)
            variant_scores[(metric, 'Retention')] = pd.concat([current_vals, prev_vals], axis=1).min(axis=1)

        return pd.DataFrame(variant_scores)

    def _normalize_metric_variants(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply minmax normalization to each metric variant column.
        TODO: Re-introduce support for other normalization methods.
        """        
        df_norm = df.copy()
        for col in df_norm.columns:
            df_norm[col] = self._minmax_scale(df_norm[col].values)
        return df_norm
    
    def _minmax_scale(self, values: np.ndarray) -> np.ndarray:
        """Min-max scaling with fallback to center_value if no range."""
        center_value = 0.5
        vmin, vmax = np.nanmin(values), np.nanmax(values)
        if vmax == vmin:
            return np.full_like(values, center_value)
        return (values - vmin) / (vmax - vmin)

    def _apply_weights_to_metric_variants(self, df: pd.DataFrame) -> pd.DataFrame:
        """Multiply metric & variant weights onto normalized data."""
        out = df.copy()
        for metric, m_weight in self.config.metrics.items():
            for variant, v_weight in self.config.metric_variants.items():
                if (metric, variant) in out.columns:
                    out[(metric, variant)] *= (m_weight * v_weight)
        return out

    def _aggregate_metric_variants(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Combine weighted, normalized metric variant columns into a single project score.
        By default, use a weighted power mean aggregator. The parameter 'p' can be tuned.
        """
        n = df.shape[1]
        out = df.copy()
    
        agg_config = getattr(self.config, 'aggregation', {})
        method = agg_config.get('method', 'power_mean') if isinstance(agg_config, dict) else 'power_mean'
        p = agg_config.get('p', 2) if isinstance(agg_config, dict) else 2
        
        if method == 'power_mean':
            if p == 0: # geometric mean (not recommended)
                epsilon = 1e-9
                out['project_score'] = np.exp(np.log(df + epsilon).mean(axis=1))
            else: # power mean
                out['project_score'] = (df.pow(p).sum(axis=1) / n)**(1/p)
        elif method == 'sum':
            out['project_score'] = df.sum(axis=1)
        else:
            raise ValueError(f"Invalid aggregation method: {method}")

        return out
    
    def _flatten_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Flattens multi-level columns after pivot/weighting.
        For tuple columns, uses contextual information to produce intuitive names:
        - For columns from the pivot table (period, metric): "Metric [Period]"
        - For metric variant columns (metric, variant): "Metric (Variant)"
        - Otherwise, joins the tuple with a hyphen.
        """
        def _flat(col):
            if isinstance(col, tuple):
                # If the first element is a period (from the pivot), e.g., "Jan 2025"
                # Format as: "metric [period]"
                if col[0] in self.config.periods:
                    return f"{col[1]} [{col[0]}]"
                # If the second element is one of our known metric variants
                # Format as: "metric - variant"
                elif col[1] in self.config.metric_variants:                    
                    return f"{col[0]} - {col[1].lower()}_variant"
                else:
                    # Fallback: join with a hyphen
                    return " - ".join(str(x) for x in col)
            return str(col)
        out = df.copy()
        out.columns = [_flat(c) for c in df.columns]
        return out


    def _prepare_final_results(
        self,
        analysis: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """Prepare final results with normalized scores and flattened columns."""
        # Calculate normalized scores
        scores_series = analysis["aggregated_project_scores"]['project_score']
        normalized_series = scores_series / scores_series.sum()
        normalized_series.name = 'weighted_score'

        # Flatten pivot tables and combine results
        df_pivoted_weighted = self._flatten_columns(analysis["pivoted_raw_metrics_weighted_by_chain"])
        df_variants = self._flatten_columns(analysis["pivoted_metric_variants"])
        df_weighted_variants = self._flatten_columns(analysis["weighted_metric_variants"])

        final_df = (
            df_pivoted_weighted
            .join(df_variants)
            .join(df_weighted_variants, lsuffix=' - weighted')
            .join(normalized_series)
            .sort_values('weighted_score', ascending=False)
        )
        
        return final_df

# ------------------------------------------------------------------------
# Load config & data
# ------------------------------------------------------------------------

def load_config(config_path: str) -> Tuple[DataSnapshot, SimulationConfig]:
    """
    Load configuration from YAML.
    Returns (DataSnapshot, SimulationConfig).
    """
    with open(config_path, 'r') as f:
        ycfg = yaml.safe_load(f)

    ds = DataSnapshot(
        data_dir=ycfg['data_snapshot'].get('data_dir', "eval-algos/S7/data/onchain_testing"),
        projects_file=ycfg['data_snapshot'].get('projects_file', "projects_v1.csv"),
        metrics_file=ycfg['data_snapshot'].get('metrics_file', "onchain_metrics_by_project.csv")
    )

    # Load simulation config directly from YAML
    sim = ycfg.get('simulation', {})
    sc = SimulationConfig(
        periods=sim.get('periods', {}),
        chains=sim.get('chains', {}),
        metrics=sim.get('metrics', {}),
        metric_variants=sim.get('metric_variants', {}),
        aggregation=sim.get('aggregation', {})
    )

    return ds, sc

def load_data(ds: DataSnapshot) -> pd.DataFrame:
    """
    Load raw CSV data, merge into single DataFrame.
    """
    def path(x: str):
        return f"{ds.data_dir}/{x}"

    df_projects = pd.read_csv(path(ds.projects_file))
    df_metrics = pd.read_csv(path(ds.metrics_file))

    df_metrics['measurement_period'] = pd.to_datetime(df_metrics['sample_date']).dt.strftime('%b %Y')
    return df_metrics.merge(df_projects, on='project_id', how='left')


# ------------------------------------------------------------------------
# Main pipeline entry-point & packaging
# ------------------------------------------------------------------------

def run_simulation(config_path: str) -> Dict[str, Any]:
    
    # Load config & data
    ds, sim_cfg = load_config(config_path)
    df_data = load_data(ds)

    # Create calculator and run analysis
    calculator = OnchainBuildersCalculator(sim_cfg)
    analysis = calculator.run_analysis(df_data)

    # Store config references
    analysis["data_snapshot"] = ds
    analysis["simulation_config"] = sim_cfg

    return analysis


# ------------------------------------------------------------------------
# Serialize
# ------------------------------------------------------------------------

def save_results(analysis: Dict[str, Any]) -> None:
    """
    Write final results to a CSV if data_snapshot is available.
    """
    ds = analysis.get("data_snapshot")
    if ds is None:
        print("No DataSnapshot found; skipping file output.")
        return

    out_path = f"{ds.data_dir}/onchain_builders_testing_results.csv"
    analysis["final_results"].to_csv(out_path, index=True)
    print(f"Saved onchain builders results to {out_path}")


# ------------------------------------------------------------------------
# main()
# ------------------------------------------------------------------------

def main():
    """
    Standard entry-point for running this script from CLI.
    """
    config_path = 'eval-algos/S7/weights/onchain_builders_testing.yaml'
    analysis = run_simulation(config_path)
    save_results(analysis)


if __name__ == "__main__":
    main()