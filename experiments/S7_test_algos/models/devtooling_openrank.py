from dataclasses import dataclass
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
import yaml
import warnings

from openrank_sdk import EigenTrust
warnings.filterwarnings('ignore', message='Defaulting to the \'raw\' score scale*')


@dataclass
class DataSnapshot:
    data_dir: str
    onchain_projects_file: str
    devtooling_projects_file: str
    project_dependencies_file: str
    developers_to_projects_file: str


@dataclass
class SimulationConfig:
    alpha: float
    time_decay: Dict[str, float]
    onchain_project_pretrust_weights: Dict[str, float]
    devtooling_project_pretrust_weights: Dict[str, float]
    event_type_weights: Dict[str, float]
    link_type_weights: Dict[str, float]
    eligibility_thresholds: Dict[str, int]


class DevtoolingCalculator:
    """
    Calculates trust scores for devtooling projects based on their relationships with onchain projects.
    
    The trust graph reflects the following flow:
    1. Onchain projects (seeded with economic pretrust) confer trust to:
       - Devtooling projects directly (via package dependency edges)
       - Developers (via commit events)
    2. Developers (seeded with reputation from onchain projects) then
       confer trust to devtooling projects (via GitHub engagement edges)
    
    The final EigenTrust propagation is seeded using a combination of:
    - Onchain project pretrust
    - Developer reputation
    - Devtooling project pretrust
    
    This ensures devtooling projects earn value by being useful to onchain projects.
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.analysis = {}

    # --------------------------------------------------------------------
    # Main pipeline (entry to final 'analysis' outputs)
    # --------------------------------------------------------------------
    def run_analysis(
        self,
        df_onchain_projects: pd.DataFrame,
        df_devtooling_projects: pd.DataFrame,
        df_project_dependencies: pd.DataFrame,
        df_developers_to_projects: pd.DataFrame
    ) -> Dict[str, pd.DataFrame]:
        """
        Run the complete analysis pipeline to calculate trust scores.

        Args:
            df_onchain_projects: DataFrame containing onchain project data
            df_devtooling_projects: DataFrame containing devtooling project data
            df_project_dependencies: DataFrame containing project dependency relationships
            df_developers_to_projects: DataFrame containing developer-project relationships

        Returns:
            Dict[str, pd.DataFrame]: Dictionary containing analysis results and intermediate data
        """
        # Store raw input data frames
        self.analysis = {
            'onchain_projects': df_onchain_projects,
            'devtooling_projects': df_devtooling_projects,
            'project_dependencies': df_project_dependencies,
            'developers_to_projects': df_developers_to_projects
        }

        # Run analysis pipeline steps
        self._build_unweighted_graph()
        self._compute_onchain_project_pretrust()
        self._compute_devtooling_project_pretrust()
        self._compute_developer_reputation()
        self._weight_edges()
        self._apply_eigentrust()
        self._rank_and_evaluate_projects()
        self._serialize_value_flow()

        return self.analysis

    # --------------------------------------------------------------------
    # Step 1: Construct an unweighted graph
    # --------------------------------------------------------------------
    def _build_unweighted_graph(self) -> None:
        """
        Build the initial unweighted directed graph with the following edges:
        1. Package Dependency: Onchain projects → Devtooling projects
        2. Commit Events: Onchain projects → Developers
        3. GitHub Engagement: Developers → Devtooling projects
        
        Also removes duplicate edges where onchain projects are also devtooling projects.
        """
        df_onchain = self.analysis['onchain_projects'].copy()
        df_devtooling = self.analysis['devtooling_projects'].copy()
        df_dependencies = self.analysis['project_dependencies'].copy()
        df_devs2projects = self.analysis['developers_to_projects'].copy()

        # Create a mapping of project_id to display name (for both onchain and devtooling)
        project_mapping = {**df_onchain.set_index('project_id')['display_name'].to_dict(),
                           **df_devtooling.set_index('project_id')['display_name'].to_dict()}

        # Use the most recent event timestamp for decay calculations
        time_ref = df_devs2projects['event_month'].max()

        # --- Part 1. Package Dependency: Onchain projects → Devtooling projects ---
        df_dependencies.rename(
            columns={
                'onchain_builder_project_id': 'i', 
                'devtooling_project_id': 'j',
                'dependency_source': 'event_type'
            },
            inplace=True
        )
        df_dependencies['event_month'] = time_ref  # Use latest timestamp (no decay for static dependencies)
        df_dependencies['i_name'] = df_dependencies['i'].map(project_mapping)
        df_dependencies['j_name'] = df_dependencies['j'].map(project_mapping)
        df_dependencies['link_type'] = 'PACKAGE_DEPENDENCY'
        
        # --- Part 2. Commit Events: Onchain projects → Developers ---
        df_devs2onchain = df_devs2projects[
            (df_devs2projects['project_id'].isin(df_onchain['project_id'])) &
            (df_devs2projects['event_type'] == 'COMMIT_CODE')
        ].copy()
        df_devs2onchain.rename(
            columns={
                'project_id': 'i',       # onchain project as source
                'developer_id': 'j',     # developer as target
                'developer_name': 'j_name'
            },
            inplace=True
        )
        df_devs2onchain['i_name'] = df_devs2onchain['i'].map(project_mapping)
        df_devs2onchain['link_type'] = 'ONCHAIN_PROJECT_TO_DEVELOPER'
        
        # --- Part 3. GitHub Engagement: Developers → Devtooling projects ---
        df_devs2tool = df_devs2projects[
            (df_devs2projects['project_id'].isin(df_devtooling['project_id']))
        ].copy()
        df_devs2tool.rename(
            columns={
                'developer_id': 'i',      # developer as source
                'project_id': 'j',        # devtooling project as target
                'developer_name': 'i_name'
            },
            inplace=True
        )
        df_devs2tool['j_name'] = df_devs2tool['j'].map(project_mapping)
        df_devs2tool['link_type'] = 'DEVELOPER_TO_DEVTOOLING_PROJECT'
        
        # --- Part 4. Remove duplicate edges if a developer's onchain project is also the devtooling project ---
        # (This prevents projects that are both onchain and devtooling from receiving extra weight.)
        onchain_devs_project_mapping = df_devs2onchain.set_index('j')['i'].to_dict()
        df_devs2tool['is_duplicate'] = df_devs2tool.apply(
            lambda row: row['i'] in onchain_devs_project_mapping and 
                        onchain_devs_project_mapping[row['i']] == row['j'], 
            axis=1
        )
        df_devs2tool = df_devs2tool[~df_devs2tool['is_duplicate']]
        df_devs2tool.drop(columns=['is_duplicate'], inplace=True)
        
        # --- Combine all edges ---
        df_dependencies['link_type'] = 'PACKAGE_DEPENDENCY'
        df_devs2onchain['link_type'] = 'ONCHAIN_PROJECT_TO_DEVELOPER'
        df_devs2tool['link_type'] = 'DEVELOPER_TO_DEVTOOLING_PROJECT'
        df_combined = pd.concat([
            df_dependencies,
            df_devs2onchain,
            df_devs2tool
        ], ignore_index=True)
        cols = ['i', 'j', 'i_name', 'j_name', 'link_type', 'event_type', 'event_month']
        self.analysis['unweighted_edges'] = df_combined[cols]

    # --------------------------------------------------------------------
    # Step 2: Seed onchain projects with economic pretrust
    # --------------------------------------------------------------------
    def _compute_onchain_project_pretrust(self) -> None:
        """
        Calculate pretrust scores for onchain projects based on economic metrics.

        Uses log scaling and minmax normalization for each metric, then combines them
        using configured weights.
        Results are stored in analysis['onchain_projects_pretrust_scores'].
        """
        df_onchain = self.analysis['onchain_projects'].copy()
        df_onchain.rename(columns={'project_id': 'i'}, inplace=True)
        wts = self.config.onchain_project_pretrust_weights
        df_onchain['v'] = 0.0
        for col, weight in wts.items():
            if col in df_onchain.columns:
                # Use log scaling then minmax normalization per metric
                df_onchain[col] = self._minmax_scale(np.log1p(df_onchain[col]))
                df_onchain['v'] += df_onchain[col] * weight
        onchain_total = df_onchain['v'].sum()
        df_onchain['v'] /= onchain_total
        self.analysis['onchain_projects_pretrust_scores'] = df_onchain

    # --------------------------------------------------------------------
    # Step 3: Seed devtooling projects with GitHub pretrust
    # --------------------------------------------------------------------
    def _compute_devtooling_project_pretrust(self) -> None:
        """
        Calculate pretrust scores for devtooling projects based on GitHub metrics.
        
        Uses log scaling and minmax normalization for each metric, then combines them
        using configured weights.
        Results are stored in analysis['devtooling_projects_pretrust_scores'].
        """
        df_devtooling = self.analysis['devtooling_projects'].copy()
        df_devtooling.rename(columns={'project_id': 'i'}, inplace=True)
        wts = self.config.devtooling_project_pretrust_weights
        df_devtooling['v'] = 0.0
        for col, weight in wts.items():
            if col in df_devtooling.columns:
                df_devtooling[col] = self._minmax_scale(np.log1p(df_devtooling[col]))
                df_devtooling['v'] += df_devtooling[col] * weight
        devtooling_total = df_devtooling['v'].sum()
        df_devtooling['v'] /= devtooling_total
        self.analysis['devtooling_projects_pretrust_scores'] = df_devtooling

    # --------------------------------------------------------------------
    # Step 4: Compute developer reputation from onchain projects
    # --------------------------------------------------------------------
    def _compute_developer_reputation(self) -> None:
        """
        Calculate developer reputation scores based on their contributions to onchain projects.
        
        Distributes onchain project trust to developers based on commit history.
        Results are stored in analysis['developer_reputation'].
        """
        project_reputation = (
            self.analysis['onchain_projects_pretrust_scores']
            .set_index('i')['v']
            .to_dict()
        )
        # Use commit events (onchain → developer) to distribute onchain trust
        commit_history = (
            self.analysis['unweighted_edges']
            .query('link_type == "ONCHAIN_PROJECT_TO_DEVELOPER"')
            .groupby(['event_month', 'j'])
            .i.unique()
        )
        reputation = {}
        for (event_month, developer), onchain_projects in commit_history.items():
            value = 0.0
            for src_project in onchain_projects:
                value += project_reputation.get(src_project, 0)
            if not len(onchain_projects):
                continue
            share = value / len(onchain_projects)
            reputation[developer] = reputation.get(developer, 0) + share

        df_dev_reputation = pd.DataFrame(
            {'developer_id': list(reputation.keys()),
             'reputation': list(reputation.values())}
        )
        dev_names = self.analysis['developers_to_projects'].set_index('developer_id')['developer_name'].to_dict()
        df_dev_reputation['developer_name'] = df_dev_reputation['developer_id'].map(dev_names)
        
        # Normalize the developer reputation scores
        df_dev_reputation['reputation'] = self._minmax_scale(df_dev_reputation['reputation'])

        self.analysis['developer_reputation'] = df_dev_reputation

    # --------------------------------------------------------------------
    # Step 5: Weight edges (including time decay)
    # --------------------------------------------------------------------
    def _weight_edges(self) -> None:
        """
        Apply weights and time decay to graph edges.
        
        Weights are applied based on:
        - Time decay (more recent events have higher weight)
        - Link type weights from config
        - Event type weights from config
        
        Results are stored in analysis['weighted_edges'].
        """
        df_edges = self.analysis['unweighted_edges'].copy()

        # Calculate time decay based on event recency
        time_ref = df_edges['event_month'].max()    
        time_diff_years = (time_ref - df_edges['event_month']).dt.days / 365.0
        
        # Default decay is 1 (no decay)
        df_edges['v_decay'] = 1.0  

        # Apply decay for onchain project → developer links
        mask_onchain = df_edges['link_type'] == 'ONCHAIN_PROJECT_TO_DEVELOPER'
        if mask_onchain.any():
            decay_factor = self.config.time_decay.get('commit_to_onchain_repo', 1.0)
            df_edges.loc[mask_onchain, 'v_decay'] = np.exp(-decay_factor * time_diff_years[mask_onchain])
            
        # Apply decay for developer → devtooling links
        mask_devtool = df_edges['link_type'] == 'DEVELOPER_TO_DEVTOOLING_PROJECT'
        if mask_devtool.any():
            decay_factor = self.config.time_decay.get('event_to_devtooling_repo', 1.0)
            df_edges.loc[mask_devtool, 'v_decay'] = np.exp(-decay_factor * time_diff_years[mask_devtool])
            
        # Weight edges by link type and event type
        df_edges['v_linktype'] = df_edges['link_type'].map(self.config.link_type_weights)
        df_edges['v_eventtype'] = df_edges['event_type'].map(self.config.event_type_weights)
        df_edges['v_final'] = df_edges['v_decay'] * df_edges['v_linktype'] * df_edges['v_eventtype']
        self.analysis['weighted_edges'] = df_edges

    # --------------------------------------------------------------------
    # Step 6: Apply EigenTrust to the weighted graph using combined pretrust scores
    # --------------------------------------------------------------------
    def _apply_eigentrust(self) -> None:
        """
        Apply EigenTrust algorithm to the weighted graph.
        
        Combines pretrust scores from:
        - Onchain projects
        - Devtooling projects
        - Developer reputation
        
        Results are stored in analysis['project_openrank_scores'].
        
        Raises:
            ValueError: If no edge records or pretrust scores are found.
        """
        alpha = self.config.alpha
        et = EigenTrust(alpha=alpha)
        
        # Combine pretrust scores from all sources
        pretrust_list = []
        
        # Add onchain projects pretrust
        onchain = self.analysis.get('onchain_projects_pretrust_scores', pd.DataFrame())
        if not onchain.empty:
            pretrust_list.extend(
                {'i': row['i'], 'v': row['v']}
                for _, row in onchain.iterrows()
                if row['v'] > 0
            )
        
        # Add devtooling projects pretrust
        devtooling = self.analysis.get('devtooling_projects_pretrust_scores', pd.DataFrame())
        if not devtooling.empty:
            pretrust_list.extend(
                {'i': row['i'], 'v': row['v']}
                for _, row in devtooling.iterrows()
                if row['v'] > 0
            )
        
        # Add developer reputation
        developers = self.analysis.get('developer_reputation', pd.DataFrame())
        if not developers.empty:
            pretrust_list.extend(
                {'i': row['developer_id'], 'v': row['reputation']}
                for _, row in developers.iterrows()
                if row['reputation'] > 0
            )
        
        # Format edge records
        df_edges = self.analysis['weighted_edges'].copy()
        df_edges = df_edges[df_edges['v_final'] > 0]
        edge_records = [
            {'i': row['i'], 'j': row['j'], 'v': row['v_final']}
            for _, row in df_edges.iterrows()
        ]
        
        if not edge_records:
            raise ValueError("No edge records found - check if v_final values are all 0 or if weighted_edges is empty")
        if not pretrust_list:
            raise ValueError("No pretrust scores found - check computed pretrust scores")
        
        # Run EigenTrust propagation
        scores = et.run_eigentrust(edge_records, pretrust_list)
        df_scores = pd.DataFrame(scores, columns=['i', 'v']).set_index('i')
        self.analysis['project_openrank_scores'] = df_scores

    # --------------------------------------------------------------------
    # Step 7: Rank and Evaluate Devtooling Projects
    # --------------------------------------------------------------------
    def _rank_and_evaluate_projects(self) -> None:
        """
        Rank and evaluate devtooling projects based on computed scores.
        
        Projects are evaluated based on:
        - OpenRank scores
        - Number of onchain package dependencies
        - Number of developer links
        - Eligibility thresholds from config
        
        Results are stored in analysis['devtooling_project_results'].
        """
        df_results = self.analysis['devtooling_projects'].copy()
        df_scores = self.analysis['project_openrank_scores'].copy()
        df_edges = self.analysis['weighted_edges']

        # Count onchain package dependency links
        df_pkg_deps = df_edges[df_edges['link_type'] == 'PACKAGE_DEPENDENCY']
        df_results['total_dependents'] = df_results['project_id'].apply(
            lambda pid: df_pkg_deps[df_pkg_deps['j'] == pid]['i'].nunique()
        )
        
        # Count developer → devtooling links
        df_dev_links = df_edges[df_edges['link_type'] == 'DEVELOPER_TO_DEVTOOLING_PROJECT']
        df_results['developer_links'] = df_results['project_id'].apply(
            lambda pid: df_dev_links[df_dev_links['j'] == pid]['i'].nunique()
        )
        
        # Apply eligibility thresholds
        thresholds = self.config.eligibility_thresholds
        df_results['is_eligible'] = 0
        df_results.loc[
            (df_results['total_dependents'] >= thresholds.get('num_projects_with_package_links', 0)) |
            (df_results['developer_links'] >= thresholds.get('num_onchain_developers_with_links', 0)),
            'is_eligible'
        ] = 1
        
        # Merge scores and compute final rankings
        df_results = df_results.merge(
            df_scores, left_on='project_id', right_on='i', how='left'
        )
        df_results['v'] = df_results['v'].fillna(0.0)
        df_results.drop_duplicates(subset=['project_id'], inplace=True)

        # Normalize final scores
        df_results['v_aggregated'] = df_results['v'] * df_results['is_eligible']
        total_score = df_results['v_aggregated'].sum()
        if total_score > 0:
            df_results['v_aggregated'] /= total_score
            
        df_results.sort_values(by='v_aggregated', ascending=False, inplace=True)
        self.analysis['devtooling_project_results'] = df_results

    # --------------------------------------------------------------------
    # Step 8: Serialize Detailed Graph with Full Relationship Info
    # --------------------------------------------------------------------
    def _serialize_value_flow(self) -> None:
        """
        Build a final graph that shows value flow between
        Onchain Projects and Devtooling Projects.

        The output DataFrame will have three columns:
          - onchain_project_id
          - devtooling_project_id
          - contribution

        For each devtooling project, the sum of contributions equals its v_aggregated.
        For each onchain project, the sum of contributions equals its economic pretrust v.
        """
        import warnings  # Ensure warnings is imported
        
        # Retrieve necessary DataFrames from the analysis dictionary.
        edges = self.analysis['weighted_edges']
        results = self.analysis['devtooling_project_results']
        onchain_projects = self.analysis['onchain_projects_pretrust_scores']

        # Build mapping from developer -> unique set of onchain projects (from commit events)
        onchain_projects_by_dev = (
            edges.query('link_type == "ONCHAIN_PROJECT_TO_DEVELOPER"')
                 .groupby('j')['i']
                 .unique()
                 .to_dict()
        )
        
        # Build a DataFrame for PACKAGE_DEPENDENCY edges (direct mapping).
        df_pkg = edges.loc[edges['link_type'] == 'PACKAGE_DEPENDENCY', ['i', 'j']].copy()

        # Build a DataFrame for DEVELOPER_TO_DEVTOOLING_PROJECT edges.
        df_dev = edges.loc[edges['link_type'] == 'DEVELOPER_TO_DEVTOOLING_PROJECT', ['i', 'j']].copy()
        # For each developer edge, map the developer (i) to its onchain projects.
        df_dev['onchain_list'] = df_dev['i'].map(lambda d: onchain_projects_by_dev.get(d, []))
        # Explode the onchain_list column and then keep only that column (renaming it to 'i') and 'j'
        df_dev_expanded = df_dev.explode('onchain_list')
        df_dev_expanded = df_dev_expanded[['onchain_list', 'j']].rename(columns={'onchain_list': 'i'})
        
        # Concatenate the two DataFrames.
        graph_df = pd.concat([df_pkg, df_dev_expanded], ignore_index=True)
        
        # Build a pivot table of counts (raw connectivity matrix) between onchain and devtooling projects.
        counts = graph_df.groupby(['i', 'j']).size().reset_index(name='count')
        pivot = counts.pivot(index='i', columns='j', values='count').fillna(0)
        onchain_ids = pivot.index.to_numpy()            # Array of onchain project IDs.
        devtooling_ids = pivot.columns.to_numpy()         # Array of devtooling project IDs.
        A = pivot.values                                  # Connectivity matrix (n_onchain x n_devtooling).

        # Get target vectors for onchain and devtooling projects.
        devtooling_project_scores = results.set_index('project_id')['v_aggregated'].to_dict()
        onchain_project_scores = onchain_projects.set_index('i')['v'].to_dict()
        v_onchain = np.array([onchain_project_scores.get(i, 0) for i in onchain_ids])
        v_devtooling = np.array([devtooling_project_scores.get(j, 0) for j in devtooling_ids])
        
        # Iterative Proportional Fitting (IPF) to allocate contributions.
        s = np.ones(len(devtooling_ids))
        tol = 1e-6
        max_iter = 1000
        for _ in range(max_iter):
            r = v_onchain / (A.dot(s) + 1e-12)
            s_new = v_devtooling / (A.T.dot(r) + 1e-12)
            if np.allclose(s_new, s, atol=tol):
                s = s_new
                break
            s = s_new
        # Compute allocated contributions matrix: X[i, j] = A[i,j] * r_i * s_j.
        X = A * r[:, np.newaxis] * s[np.newaxis, :]
        
        # Extract nonzero contributions using vectorized operations.
        i_idx, j_idx = np.nonzero(X)
        contributions = X[i_idx, j_idx]
        detailed_df = pd.DataFrame({
            'onchain_project_id': onchain_ids[i_idx],
            'devtooling_project_id': devtooling_ids[j_idx],
            'contribution': contributions
        })
        
        # (Optional) Verify that for each devtooling project, contributions sum to its v_aggregated.
        dev_sum = detailed_df.groupby('devtooling_project_id')['contribution'].sum().round(6)
        for j in devtooling_ids:
            target = devtooling_project_scores.get(j, 0)
            if abs(dev_sum.get(j, 0) - target) > 1e-4:
                warnings.warn(f"Devtooling project {j} total contribution {dev_sum.get(j, 0)} != target {target}")
        
        # (Optional) Verify that for each onchain project, contributions sum to its v.
        onchain_sum = detailed_df.groupby('onchain_project_id')['contribution'].sum().round(6)
        for i in onchain_ids:
            target = onchain_project_scores.get(i, 0)
            if abs(onchain_sum.get(i, 0) - target) > 1e-4:
                warnings.warn(f"Onchain project {i} total contribution {onchain_sum.get(i, 0)} != target {target}")
        
        # Save the detailed graph to analysis.
        self.analysis['detailed_value_flow_graph'] = detailed_df
        

    # Helper: MinMax Scaling
    # --------------------------------------------------------------------
    @staticmethod
    def _minmax_scale(values: pd.Series) -> pd.Series:
        """
        Apply min-max scaling to a series of values.
        
        Args:
            values: Input series to scale
            
        Returns:
            Scaled series with values between 0 and 1
        """
        vmin, vmax = values.min(), values.max()
        if vmax == vmin:
            return pd.Series([0.5] * len(values), index=values.index)
        return (values - vmin) / (vmax - vmin)
    

# ------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------
def load_config(config_path: str) -> Tuple[DataSnapshot, SimulationConfig]:
    """
    Load configuration from a YAML file.
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    data_snapshot = DataSnapshot(
        data_dir=config['data_snapshot'].get('data_dir', "eval-algos/S7/data/devtooling_testing_v3"),
        onchain_projects_file=config['data_snapshot'].get('onchain_projects_file', "onchain_projects.csv"),
        devtooling_projects_file=config['data_snapshot'].get('devtooling_projects_file', "devtooling_projects.csv"),
        project_dependencies_file=config['data_snapshot'].get('project_dependencies_file', "project_dependencies.csv"),
        developers_to_projects_file=config['data_snapshot'].get('developers_to_projects_file', "developers_to_projects.csv")
    )

    sim_config = config.get('simulation', {})
    simulation_config = SimulationConfig(
        alpha=sim_config.get('alpha', 0.2),
        time_decay=sim_config.get('time_decay', {}),
        onchain_project_pretrust_weights=sim_config.get('onchain_project_pretrust_weights', {}),
        devtooling_project_pretrust_weights=sim_config.get('devtooling_project_pretrust_weights', {}),
        event_type_weights=sim_config.get('event_type_weights', {}),
        link_type_weights=sim_config.get('link_type_weights', {}),
        eligibility_thresholds=sim_config.get('eligibility_thresholds', {})
    )

    return data_snapshot, simulation_config


def load_data(data_snapshot: DataSnapshot) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load data files specified in the DataSnapshot.
    """
    def get_path(filename: str) -> str:
        return f"{data_snapshot.data_dir}/{filename}"

    df_onchain_projects = pd.read_csv(get_path(data_snapshot.onchain_projects_file))
    df_devtooling_projects = pd.read_csv(get_path(data_snapshot.devtooling_projects_file))
    df_project_dependencies = pd.read_csv(get_path(data_snapshot.project_dependencies_file))
    df_developers_to_projects = pd.read_csv(get_path(data_snapshot.developers_to_projects_file))
    df_developers_to_projects['event_month'] = pd.to_datetime(df_developers_to_projects['event_month'])

    return (
        df_onchain_projects,
        df_devtooling_projects,
        df_project_dependencies,
        df_developers_to_projects
    )


def run_simulation(config_path: str) -> Dict[str, Any]:
    """
    Run the complete simulation pipeline.
    """
    data_snapshot, simulation_config = load_config(config_path)
    data = load_data(data_snapshot)
    calculator = DevtoolingCalculator(simulation_config)
    analysis = calculator.run_analysis(*data)
    analysis["data_snapshot"] = data_snapshot
    analysis["simulation_config"] = simulation_config
    return analysis


def save_results(analysis: Dict[str, Any]) -> None:
    """
    Save analysis results to CSV files.
    """
    data_snapshot = analysis.get("data_snapshot")
    if data_snapshot is None:
        print("No DataSnapshot found; skipping file output.")
        return

    # Save devtooling OpenRank results
    results_path = f"{data_snapshot.data_dir}/devtooling_openrank_results.csv"
    final_results = analysis.get("devtooling_project_results")
    if final_results is not None:
        final_results.to_csv(results_path, index=False)
        print(f"[INFO] Saved devtooling openrank results to {results_path}")
    else:
        print("[WARN] No 'final_results' to serialize.")

    # Save detailed graph data
    graph_path = f"{data_snapshot.data_dir}/detailed_devtooling_graph.csv"
    graph_data = analysis.get("weighted_edges")
    if graph_data is not None:
        graph_data.to_csv(graph_path, index=False)
        print(f"[INFO] Saved detailed graph to {graph_path}")
    else:
        print("[WARN] No 'detailed_graph' to serialize.")

    # Save value flow data
    export_path = f"{data_snapshot.data_dir}/value_flow_sankey.csv"
    detailed_df = analysis.get("detailed_value_flow_graph")
    if detailed_df is not None:
        detailed_df.to_csv(export_path, index=False)
        print(f"[INFO] Saved sankey data to {export_path}")
    else:
        print("[WARN] No 'detailed_value_flow_graph' to serialize.")

def main():
    """Run the complete analysis pipeline."""
    config_path = 'eval-algos/S7/weights/devtooling_openrank_testing.yaml'
    try:
        analysis = run_simulation(config_path)
        save_results(analysis)
    except Exception as e:
        print(f"Error during simulation: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()