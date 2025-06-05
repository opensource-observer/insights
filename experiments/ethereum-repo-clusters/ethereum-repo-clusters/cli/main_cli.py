import click
from pathlib import Path

from ..config.config_manager import ConfigManager
from ..pipeline.data_manager import DataManager
from ..processing.ai_service import AIService
from ..pipeline.repository_fetcher import RepositoryFetcherStep
from ..pipeline.summary_generator import SummaryGeneratorStep
from ..pipeline.categorizer import CategorizerStep
from ..pipeline.consolidator import ConsolidatorStep
from ..pipeline.unified_processor import UnifiedProcessor

# Initialize ConfigManager globally or pass as context
# For simplicity here, we'll initialize it where needed or once at the top.
# A more robust Click app might use a context object.
config_manager = ConfigManager() # Loads default or existing pipeline_config.json

@click.group()
@click.option('--test-mode', is_flag=True, help='Run in test mode (limits fetched repos, uses test_mode_limit from config).')
@click.pass_context
def cli(ctx, test_mode):
    """DevTooling Labels CLI for processing and categorizing repositories."""
    ctx.ensure_object(dict)
    
    # Update config if test_mode flag is set via CLI
    # This overrides the value in pipeline_config.json for this run
    if test_mode:
        config_manager.set("test_mode", True) 
        # No need to save if it's a per-run override. 
        # If we want to persist it: config_manager.save_config()
        print(f"CLI flag --test-mode is set. Running in test mode. Limit: {config_manager.get_test_mode_limit()} repos.")
    else:
        # If not set by CLI, respect the config file's test_mode setting
        # Or, explicitly set to False if CLI should always override to False when flag not present
        # config_manager.set("test_mode", False) # Uncomment if CLI flag absence means test_mode is OFF
        pass # Current behavior: respects config file if CLI flag is absent.

    # Initialize services and pass them via context if needed by multiple commands
    # Or initialize them within each command
    output_dir = config_manager.get_output_dir()
    data_manager = DataManager(output_dir=output_dir, config=config_manager)
    ai_service = AIService(config_manager=config_manager)
    
    ctx.obj['config_manager'] = config_manager
    ctx.obj['data_manager'] = data_manager
    ctx.obj['ai_service'] = ai_service
    ctx.obj['output_dir'] = output_dir


@cli.command("fetch_repos")
@click.option('--force-refresh', is_flag=True, help='Force refresh repository data, ignoring existing.')
@click.option('--fetch-new-only', is_flag=True, help='Only fetch repositories that don\'t exist in current data.')
@click.pass_context
def fetch_repos_command(ctx, force_refresh, fetch_new_only):
    """Fetches repositories and their READMEs."""
    print("Executing: Fetch Repositories")
    data_manager = ctx.obj['data_manager']
    # ConfigManager is already aware of test_mode from the group command
    config_mgr = ctx.obj['config_manager'] 
    
    repo_fetcher_step = RepositoryFetcherStep(data_manager=data_manager, config_manager=config_mgr)
    repo_fetcher_step.run(force_refresh=force_refresh, fetch_new_only=fetch_new_only)
    print("Repository fetching complete.")


@cli.command("generate_summaries")
@click.option('--force-refresh', is_flag=True, help='Force refresh summaries, ignoring existing.')
@click.option('--new-only', is_flag=True, help='Generate summaries only for repositories that don\'t have summaries yet.')
@click.pass_context
def generate_summaries_command(ctx, force_refresh, new_only):
    """Generates summaries for the fetched repositories."""
    print("Executing: Generate Summaries")
    data_manager = ctx.obj['data_manager']
    config_mgr = ctx.obj['config_manager']
    ai_service = ctx.obj['ai_service']
    
    summary_generator_step = SummaryGeneratorStep(
        data_manager=data_manager, 
        config_manager=config_mgr, 
        ai_service=ai_service
    )
    summary_generator_step.run(force_refresh=force_refresh, new_only=new_only)
    print("Summary generation complete.")


@cli.command("categorize")
@click.option('--force-refresh', is_flag=True, help='Force refresh categories, ignoring existing.')
@click.option('--persona', help='Process only the specified persona.')
@click.option('--new-only', is_flag=True, help='Categorize only repositories that don\'t have categories yet.')
@click.pass_context
def categorize_command(ctx, force_refresh, persona, new_only):
    """Categorizes projects using AI personas."""
    print("Executing: Categorize")
    data_manager = ctx.obj['data_manager']
    config_mgr = ctx.obj['config_manager']
    ai_service = ctx.obj['ai_service']
    
    categorizer_step = CategorizerStep(
        data_manager=data_manager, 
        config_manager=config_mgr, 
        ai_service=ai_service
    )
    categorizer_step.run(force_refresh=force_refresh, target_persona_name=persona, new_only=new_only)
    print("Categorization complete.")


@cli.command("consolidate")
@click.pass_context
def consolidate_command(ctx):
    """Consolidates categorizations and generates final recommendations."""
    print("Executing: Consolidate Analysis")
    data_manager = ctx.obj['data_manager']
    config_mgr = ctx.obj['config_manager']
    
    consolidator_step = ConsolidatorStep(data_manager=data_manager, config_manager=config_mgr)
    consolidator_step.run()
    print("Consolidation complete.")


@cli.command("process_unified")
@click.option('--force-refresh', is_flag=True, help='Force refresh all data, ignoring existing.')
@click.option('--include-forks', is_flag=True, help='Include forked repositories in processing.')
@click.option('--include-inactive', is_flag=True, help='Include repositories not updated in the last year.')
@click.option('--limit', type=int, help='Limit the number of repositories to process.')
@click.pass_context
def process_unified_command(ctx, force_refresh, include_forks, include_inactive, limit):
    """
    Unified processing: fetches repos, READMEs, generates summaries, and categorizes in one pass.
    Outputs a single comprehensive dataset with all information.
    """
    print("Executing: Unified Processing Pipeline")
    data_manager = ctx.obj['data_manager']
    config_mgr = ctx.obj['config_manager']
    ai_service = ctx.obj['ai_service']
    
    processor = UnifiedProcessor(
        data_manager=data_manager,
        config_manager=config_mgr,
        ai_service=ai_service
    )
    
    processor.run(
        force_refresh=force_refresh,
        include_forks=include_forks,
        inactive_repos=include_inactive,
        limit=limit
    )
    
    print("Unified processing complete.")
    print(f"Results saved to:")
    print(f"  - {data_manager.unified_parquet_path} (Parquet format)")
    print(f"  - {data_manager.unified_csv_path} (CSV format)")


@cli.command("run_all")
@click.option('--force-refresh-all', is_flag=True, help='Force refresh all data stages.')
@click.option('--force-refresh-repos', is_flag=True, help='Force refresh repository data.')
@click.option('--force-refresh-summaries', is_flag=True, help='Force refresh summaries.')
@click.option('--force-refresh-categories', is_flag=True, help='Force refresh categories.')
@click.option('--use-unified', is_flag=True, help='Use the new unified processor instead of the legacy pipeline.')
@click.option('--include-forks', is_flag=True, help='Include forked repositories (only with --use-unified).')
@click.option('--include-inactive', is_flag=True, help='Include inactive repositories (only with --use-unified).')
@click.pass_context
def run_all_command(ctx, force_refresh_all, force_refresh_repos, force_refresh_summaries, 
                   force_refresh_categories, use_unified, include_forks, include_inactive):
    """Runs the entire pipeline: either legacy steps or the new unified processor."""
    
    if use_unified:
        print("Executing: Run All Using Unified Processor")
        ctx.invoke(
            process_unified_command, 
            force_refresh=force_refresh_all, 
            include_forks=include_forks,
            include_inactive=include_inactive,
            limit=None
        )
    else:
        print("Executing: Run All Pipeline Steps (Legacy)")
        # Determine force_refresh flags for each step
        fr_repos = force_refresh_all or force_refresh_repos
        fr_summaries = force_refresh_all or force_refresh_summaries
        fr_categories = force_refresh_all or force_refresh_categories

        # Invoke other commands with determined force_refresh settings
        # The --test-mode flag from the main group is implicitly handled by ConfigManager
        ctx.invoke(fetch_repos_command, force_refresh=fr_repos)
        ctx.invoke(generate_summaries_command, force_refresh=fr_summaries)
        ctx.invoke(categorize_command, force_refresh=fr_categories, persona=None, new_only=False) # Process all personas
        ctx.invoke(consolidate_command)
    
    print("Full pipeline execution complete.")

# Commands for managing personas in config
@cli.group("personas")
def personas_group():
    """Manage AI personas in the configuration."""
    pass

@personas_group.command("list")
@click.pass_context
def list_personas(ctx):
    """Lists all configured personas."""
    config_mgr = ctx.obj['config_manager']
    personas = config_mgr.get_personas()
    if not personas:
        print("No personas configured.")
        return
    print("Configured Personas:")
    for p in personas:
        print(f"- Name: {p['name']}, Title: {p.get('title', 'N/A')}")

@personas_group.command("add")
@click.option('--name', required=True, help="Unique name for the persona.")
@click.option('--title', required=True, help="Display title for the persona.")
@click.option('--description', required=True, help="Description of the persona's focus.")
@click.option('--prompt-template', required=True, help="Prompt template for the persona's classification task.")
@click.pass_context
def add_persona(ctx, name, title, description, prompt_template):
    """Adds a new persona to the configuration."""
    config_mgr = ctx.obj['config_manager']
    new_persona = {
        "name": name,
        "title": title,
        "description": description,
        "prompt": prompt_template
    }
    # config_mgr.add_persona(new_persona) # This method was removed as personas are managed in personas.py
    print(f"Persona management is now done by editing devtooling_labels/config/prompts/personas.py. '{name}' was not added via CLI.")
    print("To add a persona, please edit the personas.py file directly.")

@personas_group.command("remove")
@click.argument('name')
@click.pass_context
def remove_persona(ctx, name):
    """Removes a persona by name. (Note: Persona management is now via personas.py)"""
    # config_mgr = ctx.obj['config_manager']
    # config_mgr.remove_persona(name) # This method was removed from ConfigManager
    print(f"Persona management is now done by editing devtooling_labels/config/prompts/personas.py. '{name}' was not removed via CLI.")
    print("To remove a persona, please edit the personas.py file directly.")

if __name__ == '__main__':
    cli(obj={})
