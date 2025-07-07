import pandas as pd
import os
from typing import Dict, List, Tuple


def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load the m5_dependencies.csv and direct_dependencies.csv files."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load m5_dependencies.csv
    m5_path = os.path.join(script_dir, "m5_dependencies.csv")
    m5_df = pd.read_csv(m5_path)
    
    # Load direct_dependencies.csv
    direct_path = os.path.join(script_dir, "direct_dependencies.csv")
    direct_df = pd.read_csv(direct_path)
    
    return m5_df, direct_df


def analyze_dependency_coverage(m5_df: pd.DataFrame, direct_df: pd.DataFrame) -> pd.DataFrame:
    """Analyze what percentage of each package's dependencies are direct dependencies."""
    
    # Get unique dependency names from m5_dependencies.csv
    target_dependencies = set(m5_df['dependency_name'].unique())
    
    # Get unique package names from direct_dependencies.csv
    direct_packages = set(direct_df['package_name'].unique())
    
    # Calculate statistics for each target dependency
    results = []
    
    for dep_name in sorted(target_dependencies):
        # Count total occurrences in m5_dependencies.csv
        total_occurrences = len(m5_df[m5_df['dependency_name'] == dep_name])
        
        # Count direct dependencies found
        direct_occurrences = len(direct_df[direct_df['package_name'] == dep_name])
        
        # Calculate percentage
        percentage = (direct_occurrences / total_occurrences * 100) if total_occurrences > 0 else 0
        
        # Get list of repositories that use this dependency
        repos_using = m5_df[m5_df['dependency_name'] == dep_name]['onchain_builder_repo'].tolist()
        
        # Get list of repositories that have this as direct dependency
        repos_with_direct = direct_df[direct_df['package_name'] == dep_name]['repository'].tolist()
        
        results.append({
            'package_name': dep_name,
            'total_occurrences': total_occurrences,
            'direct_occurrences': direct_occurrences,
            'percentage_direct': round(percentage, 2),
            'repos_using': repos_using,
            'repos_with_direct': repos_with_direct,
            'missing_repos': [repo for repo in repos_using if repo not in repos_with_direct]
        })
    
    # Create DataFrame and sort by direct occurrences descending
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('direct_occurrences', ascending=False)
    
    return results_df


def print_summary(results_df: pd.DataFrame):
    """Print a summary of the analysis."""
    print("=" * 80)
    print("DEPENDENCY COVERAGE ANALYSIS")
    print("=" * 80)
    print(f"Total target dependencies: {len(results_df)}")
    print(f"Total direct dependencies found: {results_df['direct_occurrences'].sum()}")
    print(f"Total occurrences in m5_dependencies.csv: {results_df['total_occurrences'].sum()}")
    print(f"Overall coverage: {results_df['direct_occurrences'].sum() / results_df['total_occurrences'].sum() * 100:.2f}%")
    print()
    
    # Show top packages by direct occurrences
    print("TOP 10 PACKAGES BY NUMBER OF DIRECT DEPENDENCIES:")
    print("-" * 60)
    top_10 = results_df.head(10)
    for _, row in top_10.iterrows():
        print(f"{row['package_name']:<30} {row['direct_occurrences']:>3} direct ({row['percentage_direct']:>5.1f}% of {row['total_occurrences']} total)")
    
    print()
    
    # Show packages with 0% coverage
    zero_coverage = results_df[results_df['percentage_direct'] == 0]
    if len(zero_coverage) > 0:
        print(f"PACKAGES WITH 0% COVERAGE ({len(zero_coverage)}):")
        print("-" * 40)
        for _, row in zero_coverage.iterrows():
            print(f"  {row['package_name']} ({row['total_occurrences']} occurrences)")
    
    print()


def save_detailed_results(results_df: pd.DataFrame):
    """Save detailed results to CSV files."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Save main results
    main_results = results_df[['package_name', 'total_occurrences', 'direct_occurrences', 'percentage_direct']].copy()
    main_results.to_csv(os.path.join(script_dir, "dependency_coverage_analysis.csv"), index=False)
    
    # Save detailed results with repository lists
    detailed_results = results_df.copy()
    detailed_results['repos_using'] = detailed_results['repos_using'].apply(lambda x: '; '.join(x))
    detailed_results['repos_with_direct'] = detailed_results['repos_with_direct'].apply(lambda x: '; '.join(x))
    detailed_results['missing_repos'] = detailed_results['missing_repos'].apply(lambda x: '; '.join(x))
    detailed_results.to_csv(os.path.join(script_dir, "dependency_coverage_detailed.csv"), index=False)
    
    print(f"Results saved to:")
    print(f"  - dependency_coverage_analysis.csv (summary)")
    print(f"  - dependency_coverage_detailed.csv (detailed with repository lists)")


def main():
    """Main analysis function."""
    print("Loading data...")
    m5_df, direct_df = load_data()
    
    print(f"Loaded {len(m5_df)} dependency records from m5_dependencies.csv")
    print(f"Loaded {len(direct_df)} direct dependency records")
    print()
    
    print("Analyzing dependency coverage...")
    results_df = analyze_dependency_coverage(m5_df, direct_df)
    
    # Print summary
    print_summary(results_df)
    
    # Save results
    save_detailed_results(results_df)
    
    # Display full results table
    print("FULL RESULTS (sorted by number of direct dependencies descending):")
    print("=" * 80)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    
    display_df = results_df[['package_name', 'total_occurrences', 'direct_occurrences', 'percentage_direct']].copy()
    print(display_df.to_string(index=False))


if __name__ == "__main__":
    main()
