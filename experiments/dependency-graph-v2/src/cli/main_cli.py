import click
from pathlib import Path

from ..config.config_manager import ConfigManager
from ..pipeline.data_manager import DataManager
from ..pipeline.repository_manager import RepositoryManager
from .interactive_workflow import InteractiveWorkflow

# Initialize ConfigManager globally or pass as context
config_manager = ConfigManager() # Loads default or existing pipeline_config.json

@click.group()
@click.option('--test-mode', is_flag=True, help='Run in test mode (limits fetched repos, uses test_mode_limit from config).')
@click.pass_context
def cli(ctx, test_mode):
    """Dependency Graph CLI for analyzing repository dependencies."""
    ctx.ensure_object(dict)
    
    # Update config if test_mode flag is set via CLI
    if test_mode:
        config_manager.set("test_mode", True) 
        print(f"CLI flag --test-mode is set. Running in test mode. Limit: {config_manager.get_test_mode_limit()} repos.")
    else:
        # If not set by CLI, respect the config file's test_mode setting
        pass # Current behavior: respects config file if CLI flag is absent.

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
