import click
from pathlib import Path

from ..config.config_manager import ConfigManager
from ..pipeline.data_manager import DataManager
from ..pipeline.repository_manager import RepositoryManager
from .interactive_workflow import InteractiveWorkflow

# Initialize ConfigManager globally or pass as context
config_manager = ConfigManager() 

@click.group()
@click.option('--test-mode', is_flag=True, help='Run in test mode (limits fetched repos, uses test_mode_limit from config).')
@click.pass_context
def cli(ctx, test_mode):
    """Dependency Graph CLI for analyzing repository dependencies."""
    ctx.ensure_object(dict)
    
    # Handle test mode flag
    if test_mode:
        print(f"CLI flag --test-mode is set. Running in test mode. Limit: {config_manager.get_test_mode_limit()} repos.")
        # Note: Test mode is now controlled by settings.py, not runtime configuration
    else:
        # Test mode is controlled by the TEST_MODE setting in settings.py
        if config_manager.is_test_mode():
            print(f"Test mode is enabled in settings. Limit: {config_manager.get_test_mode_limit()} repos.")

    # Initialize services and pass them via context
    output_dir = config_manager.get_output_dir()
    data_manager = DataManager(output_dir=output_dir, config=config_manager)
    
    ctx.obj['config_manager'] = config_manager
    ctx.obj['data_manager'] = data_manager
    ctx.obj['output_dir'] = output_dir




@cli.group("dependencies")
def dependencies_group():
    """Manage repository dependencies."""
    pass

@dependencies_group.command("fetch")
@click.option('--repo-url', help='Fetch dependencies for a specific repository.')
@click.option('--source', type=click.Choice(['github_api', 'package_files', 'sbom', 'all']), default='all', 
              help='Dependency source to use.')
@click.option('--overwrite', is_flag=True, help='Overwrite existing dependency data.')
@click.option('--no-merge', is_flag=True, help="Don't merge with existing dependencies from other sources.")
@click.pass_context
def fetch_dependencies(ctx, repo_url, source, overwrite, no_merge):
    """Fetch dependencies for repositories."""
    print("Executing: Fetch Dependencies")
    data_manager = ctx.obj['data_manager']
    config_mgr = ctx.obj['config_manager']
    
    repo_manager = RepositoryManager()
    
    # Determine which repositories to process
    if repo_url:
        repo_urls = [repo_url]
        if repo_url not in repo_manager.get_all_repos():
            print(f"Repository {repo_url} not found in repository sources.")
            if click.confirm("Add repository to repository sources?", default=True):
                repo_manager.add_repo(repo_url)
            else:
                print("Aborted.")
                return
    else:
        repo_urls = None  # Process all repositories
    
    # Determine which sources to use
    if source == 'github_api':
        sources = ['github_api']
    elif source == 'package_files':
        sources = ['package_files']
    elif source == 'sbom':
        sources = ['sbom']
    else:  # 'all'
        sources = ['github_api', 'package_files', 'sbom']
    
    # Fetch dependencies
    dependencies = repo_manager.fetch_dependencies(
        repo_urls=repo_urls, 
        sources=sources,
        merge_with_existing=not no_merge
    )
    
    # Save dependencies
    data_manager.save_dependencies(dependencies, overwrite=overwrite)
    
    # Update repository status
    for repo_url, deps in dependencies.items():
        data_manager.update_repo_status(
            repo_url,
            f"Dependencies fetched: {len(deps)} dependencies found"
        )
    
    print("Dependency fetching complete.")

@dependencies_group.command("import-sbom")
@click.argument('sbom_file')
@click.argument('repo_url')
@click.option('--overwrite', is_flag=True, help='Overwrite existing dependency data.')
@click.pass_context
def import_sbom(ctx, sbom_file, repo_url, overwrite):
    """Import dependencies from an SPDX SBOM file (JSON format)."""
    print(f"Importing SBOM file: {sbom_file}")
    data_manager = ctx.obj['data_manager']
    config_mgr = ctx.obj['config_manager']
    
    repo_manager = RepositoryManager()
    
    # Check if the repository exists in repository sources
    if repo_url not in repo_manager.get_all_repos():
        print(f"Repository {repo_url} not found in repository sources.")
        if click.confirm("Add repository to repository sources?", default=True):
            repo_manager.add_repo(repo_url)
        else:
            print("Aborted.")
            return
    
    # Import SBOM file
    sbom_path = Path(sbom_file)
    if not sbom_path.exists():
        print(f"Error: SBOM file {sbom_file} not found.")
        return
    
    # Extract dependencies from SBOM
    dependencies = repo_manager.import_sbom(sbom_file, repo_url)
    if not dependencies:
        print("No dependencies found in SBOM file.")
        return
    
    print(f"Found {len(dependencies)} dependencies in SBOM file.")
    
    # Save dependencies
    data_manager.save_dependencies(
        {repo_url: dependencies},
        overwrite=overwrite
    )
    
    # Update repository status
    data_manager.update_repo_status(
        repo_url,
        f"SBOM imported: {len(dependencies)} dependencies found"
    )
    
    print(f"Successfully imported SBOM for {repo_url}.")

@dependencies_group.command("import-csv")
@click.argument('csv_file')
@click.argument('repo_url')
@click.option('--overwrite', is_flag=True, help='Overwrite existing dependency data.')
@click.pass_context
def import_csv(ctx, csv_file, repo_url, overwrite):
    """Import dependencies from a CSV SBOM export from GitHub."""
    print(f"Importing CSV file: {csv_file}")
    data_manager = ctx.obj['data_manager']
    config_mgr = ctx.obj['config_manager']
    
    repo_manager = RepositoryManager()
    
    # Check if the repository exists in repository sources
    if repo_url not in repo_manager.get_all_repos():
        print(f"Repository {repo_url} not found in repository sources.")
        if click.confirm("Add repository to repository sources?", default=True):
            repo_manager.add_repo(repo_url)
        else:
            print("Aborted.")
            return
    
    # Import CSV file
    csv_path = Path(csv_file)
    if not csv_path.exists():
        print(f"Error: CSV file {csv_file} not found.")
        return
    
    # Extract dependencies from CSV
    dependencies = repo_manager.import_sbom(csv_file, repo_url)
    if not dependencies:
        print("No dependencies found in CSV file.")
        return
    
    print(f"Found {len(dependencies)} dependencies in CSV file.")
    
    # Save dependencies
    data_manager.save_dependencies(
        {repo_url: dependencies},
        overwrite=overwrite
    )
    
    # Update repository status
    data_manager.update_repo_status(
        repo_url,
        f"CSV SBOM imported: {len(dependencies)} dependencies found"
    )
    
    print(f"Successfully imported CSV SBOM for {repo_url}.")

@dependencies_group.command("add-file")
@click.argument('repo_url')
@click.argument('file_url')
@click.pass_context
def add_dependency_file(ctx, repo_url, file_url):
    """Add a dependency file to a repository."""
    repo_manager = RepositoryManager()
    
    # Check if the repository exists in repository sources
    if repo_url not in repo_manager.get_all_repos():
        print(f"Repository {repo_url} not found in repository sources.")
        if click.confirm("Add repository to repository sources?", default=True):
            repo_manager.add_repo(repo_url)
        else:
            print("Aborted.")
            return
    
    # Add dependency file
    if repo_manager.add_dependency_file(repo_url, file_url):
        print(f"Added dependency file {file_url} to {repo_url}.")
    else:
        print(f"Failed to add dependency file or file already exists.")

@dependencies_group.command("list-repos")
@click.pass_context
def list_repos(ctx):
    """List all repositories in repository sources."""
    repo_manager = RepositoryManager()
    repos = repo_manager.get_all_repos()
    
    if not repos:
        print("No repositories found.")
        return
    
    print("Repositories:")
    for repo in repos:
        print(f"- {repo}")

@dependencies_group.command("status")
@click.option('--repo-url', help='Show status for a specific repository.')
@click.pass_context
def repo_status(ctx, repo_url):
    """Show repository status."""
    data_manager = ctx.obj['data_manager']
    
    if repo_url:
        status = data_manager.get_repo_status(repo_url)
        if status:
            print(f"Status for {repo_url}: {status}")
        else:
            print(f"No status found for {repo_url}.")
    else:
        status_data = data_manager.get_repo_status()
        if not status_data:
            print("No repository status data found.")
            return
        
        print("Repository Status:")
        for url, status in status_data.items():
            print(f"- {url}: {status}")

@dependencies_group.command("generate-snapshot")
@click.pass_context
def generate_snapshot(ctx):
    """Generate a dependency snapshot across all repositories."""
    from ..pipeline.dependency_snapshot import DependencySnapshot
    import json
    import os
    
    print("Generating dependency snapshot...")
    data_manager = ctx.obj['data_manager']
    
    # Get all dependencies from the dependencies.json file
    try:
        with open(data_manager.dependencies_path, 'r') as f:
            dependencies_data = json.load(f)
        
        # Create snapshot
        snapshot = DependencySnapshot(dependencies_data)
        
        # Save snapshot
        output_path = os.path.join(data_manager.output_dir, "dependency_snapshot.json")
        snapshot.save_snapshot(output_path)
        
        print(f"Dependency snapshot saved to {output_path}")
        
        # Print summary
        full_snapshot = snapshot.generate_full_snapshot()
        
        print("\nDependency Snapshot Summary:")
        print(f"Total repositories: {full_snapshot['total_repositories']}")
        print(f"Total dependencies: {full_snapshot['total_dependencies']}")
        
        print("\nTop 5 languages:")
        languages = sorted(
            full_snapshot['by_language'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        for language, count in languages:
            print(f"- {language}: {count}")
        
        print("\nTop 5 package managers:")
        package_managers = sorted(
            full_snapshot['by_package_manager'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        for package_manager, count in package_managers:
            print(f"- {package_manager}: {count}")
    except Exception as e:
        print(f"Error generating dependency snapshot: {str(e)}")

@dependencies_group.command("map-to-github")
@click.option('--input-file', default="output/dependencies.json", help='Input dependencies file path.')
@click.option('--output-file', default="output/dependencies_with_github.json", help='Output file path for dependencies with GitHub URLs.')
@click.pass_context
def map_to_github(ctx, input_file, output_file):
    """Map dependencies to their source GitHub repositories using OSO."""
    from ..scripts.map_dependencies_to_github import setup_oso_client, process_dependencies, load_cache, query_oso_for_packages, merge_dependency_urls
    import json
    import pandas as pd
    
    print("Mapping dependencies to GitHub repositories using OSO...")
    data_manager = ctx.obj['data_manager']
    
    try:
        # Set up OSO client
        print("Setting up OSO client...")
        client = setup_oso_client()
        print("OSO client setup complete.")
        
        # Load dependencies
        dependencies_path = Path(input_file)
        if not dependencies_path.exists():
            print(f"Error: Dependencies file not found at {dependencies_path}")
            return
        
        print(f"Loading dependencies from {dependencies_path}...")
        with open(dependencies_path, 'r') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} repositories with dependencies.")
        
        # Process dependencies
        df_deps = process_dependencies(data)
        
        # Load cache
        cache_df = load_cache()
        
        # Query OSO for packages
        df_packages = query_oso_for_packages(client, df_deps, cache_df)
        
        # Merge dependency URLs
        result = merge_dependency_urls(df_deps, df_packages)
        
        # Convert back to original format
        print("Converting results back to original format...")
        updated_data = []
        mapped_count = 0
        unknown_count = 0
        
        for seed_node in data:
            repo_url = seed_node.get('repo_url', 'Unknown')
            updated_seed_node = seed_node.copy()
            updated_dependencies = []
            
            deps = seed_node.get('dependencies', [])
            repo_mapped = 0
            repo_unknown = 0
            
            for dep in deps:
                updated_dep = dep.copy()
                
                # Find the corresponding row in the result DataFrame
                package_name = dep.get('packageName', '').lower()
                package_source = dep.get('packageManager', '')
                
                if package_name and package_source:
                    matches = result[
                        (result['package_name'] == package_name) & 
                        (result['package_source'] == package_source)
                    ]
                    
                    if not matches.empty:
                        # Get the first match (there should only be one)
                        match = matches.iloc[0]
                        github_url = match.get('dependency_github_url')
                        if github_url and pd.notna(github_url):
                            updated_dep['github_repo'] = github_url
                            mapped_count += 1
                            repo_mapped += 1
                        else:
                            updated_dep['github_repo'] = "unknown"
                            unknown_count += 1
                            repo_unknown += 1
                    else:
                        updated_dep['github_repo'] = "unknown"
                        unknown_count += 1
                        repo_unknown += 1
                else:
                    updated_dep['github_repo'] = "unknown"
                    unknown_count += 1
                    repo_unknown += 1
                
                updated_dependencies.append(updated_dep)
            
            updated_seed_node['dependencies'] = updated_dependencies
            updated_data.append(updated_seed_node)
            
            print(f"Repository {repo_url}: {repo_mapped} mapped, {repo_unknown} unknown")
        
        # Save updated dependencies
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(updated_data, f, indent=2)
        
        print(f"\nDone! Updated dependencies saved to {output_path}")
        
        # Print summary
        total_deps = sum(len(repo_data.get("dependencies", [])) for repo_data in updated_data)
        mapped_deps = sum(
            sum(1 for dep in repo_data.get("dependencies", []) if dep.get("github_repo") != "unknown")
            for repo_data in updated_data
        )
        unknown_deps = total_deps - mapped_deps
        
        print(f"\nSummary:")
        print(f"  Total dependencies: {total_deps}")
        mapped_percentage = (mapped_deps / total_deps) * 100 if total_deps > 0 else 0
        unknown_percentage = (unknown_deps / total_deps) * 100 if total_deps > 0 else 0
        print(f"  Mapped to GitHub: {mapped_deps} ({mapped_percentage:.1f}%)")
        print(f"  Unknown: {unknown_deps} ({unknown_percentage:.1f}%)")
        
    except Exception as e:
        print(f"Error: {str(e)}")

@dependencies_group.command("clean")
@click.option('--input-file', default="output/dependencies_with_github.json", help='Input dependencies file path.')
@click.option('--output-file', default="output/cleaned_dependencies.json", help='Output file path for cleaned dependencies.')
@click.pass_context
def clean_dependencies(ctx, input_file, output_file):
    """Clean and flatten the dependencies data."""
    from ..scripts.clean_dependencies import process_dependencies
    import json
    
    print("Cleaning dependencies data...")
    data_manager = ctx.obj['data_manager']
    
    try:
        # Load input file
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"Error: Input file not found at {input_path}")
            return
        
        print(f"Loading dependencies from {input_path}...")
        with open(input_path, 'r') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} repositories with dependencies.")
        
        # Process and flatten data
        cleaned_records = process_dependencies(data)
        total_dependencies = sum(len(repo_data.get('dependencies', [])) for repo_data in data)
        
        # Write output file
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(cleaned_records, f, indent=2)
        
        print(f"\nDone! Cleaned {len(cleaned_records)} dependency records.")
        print(f"Output saved to {output_path}")
        
        # Print summary
        print(f"\nSummary:")
        print(f"  Total repositories: {len(data)}")
        print(f"  Total dependencies: {total_dependencies}")
        print(f"  Cleaned records: {len(cleaned_records)}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

@dependencies_group.command("analyze-repo")
@click.argument('repo_url', required=False)
@click.pass_context
def analyze_repo(ctx, repo_url):
    """Interactive workflow to analyze a repository's dependencies."""
    print("Starting interactive repository analysis workflow...")
    data_manager = ctx.obj['data_manager']
    repo_manager = RepositoryManager()
    
    workflow = InteractiveWorkflow(data_manager=data_manager, repo_manager=repo_manager)
    workflow.run(repo_url=repo_url)


if __name__ == '__main__':
    cli(obj={})
