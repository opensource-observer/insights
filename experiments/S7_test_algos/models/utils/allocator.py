import pandas as pd
from dataclasses import dataclass


BUDGET_TOLERANCE = 1.0 / 1_000_000  # Required precision for budget allocation
MAX_NORM_ITERATIONS = 100  # Prevent infinite loops

@dataclass
class AllocationConfig:
    budget: float
    min_amount_per_project: float
    max_share_per_project: float
    max_iterations: int = 50

def allocate_with_constraints(
    project_scores: pd.Series,
    config: AllocationConfig,
    print_results: bool = True,
    rounding: int = 2,
) -> pd.Series:
    """
    Iteratively allocates the budget while enforcing constraints.
    
    Args:
        project_scores: Series with project names as index and normalized scores as values (should sum to 1.0)
        config: AllocationConfig with budget and constraint parameters
        print_results: Whether to print the results
        rounding: Number of decimal places to round allocations to
    
    Returns:
        Series with final allocations per project
    """
    # Verify scores are normalized
    if abs(project_scores.sum() - 1.0) > 1e-6:
        raise ValueError("Project scores must be normalized to sum to 1.0")

    # 1. Initial allocation based on normalized scores
    allocations = project_scores * config.budget
    max_per_project = config.max_share_per_project * config.budget
    
    # 2. Cap projects above max and redistribute excess
    while True:
        over_max = allocations > max_per_project
        if not over_max.any():
            break
            
        excess = (allocations[over_max] - max_per_project).sum()
        allocations[over_max] = max_per_project
        
        # Redistribute excess to projects under max
        under_max = allocations < max_per_project
        if under_max.any():
            remaining_scores = project_scores[under_max]
            remaining_scores = remaining_scores / remaining_scores.sum()
            allocations[under_max] += remaining_scores * excess
    
    # 3. Remove projects below min and redistribute
    while True:
        below_min = (allocations > 0) & (allocations < config.min_amount_per_project)
        if not below_min.any():
            break
            
        excess = allocations[below_min].sum()
        allocations[below_min] = 0
        
        # Redistribute to remaining projects proportionally
        active_projects = allocations > 0
        if active_projects.any():
            space_to_max = max_per_project - allocations[active_projects]
            if space_to_max.sum() > 0:
                remaining_scores = project_scores[active_projects]
                remaining_scores = remaining_scores / remaining_scores.sum()
                additional = remaining_scores * excess
                additional = additional.clip(upper=space_to_max)
                allocations[active_projects] += additional
    
    # 4. Final max cap pass
    over_max = allocations > max_per_project
    if over_max.any():
        excess = (allocations[over_max] - max_per_project).sum()
        allocations[over_max] = max_per_project
        
        # Redistribute any remaining excess to projects under max
        under_max = (allocations > 0) & (allocations < max_per_project)
        if under_max.any():
            space_to_max = max_per_project - allocations[under_max]
            remaining_scores = project_scores[under_max]
            remaining_scores = remaining_scores / remaining_scores.sum()
            additional = remaining_scores * excess
            additional = additional.clip(upper=space_to_max)
            allocations[under_max] += additional

    # 5. Final normalization to exactly match budget
    norm_iteration = 0
    while abs(allocations.sum() - config.budget) > BUDGET_TOLERANCE and norm_iteration < MAX_NORM_ITERATIONS:
        if allocations.sum() > 0:
            scale_factor = config.budget / allocations.sum()
            allocations = allocations * scale_factor
            # Clip to ensure we don't exceed max after scaling
            allocations = allocations.clip(upper=max_per_project)
        norm_iteration += 1
    
    allocations = allocations.round(rounding)
    if print_results:
        print_results_to_terminal(allocations, config)
    return allocations


def print_results_to_terminal(
    allocations: pd.Series,
    config: AllocationConfig
) -> None:
    """
    Prints the results of the allocation.
    
    Args:
        allocations: Series with project names as index and allocations as values
        config: AllocationConfig with budget and constraint parameters
    """
    print("\n=== Final Project Allocations ===")
    print(allocations.sort_values(ascending=False).head(20))
    print("\n=== Bottom 10 Projects with Rewards ===")
    print(allocations[allocations > 0].sort_values().head(10))
    
    projects_below_min = (allocations < config.min_amount_per_project).sum()
    print(f"\nNumber of projects below minimum ({config.min_amount_per_project}): {projects_below_min}")
    print(f"\nTotal Budget Allocated: {allocations.sum():,.0f} / {config.budget:,.0f}") 
