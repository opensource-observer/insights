from collections import defaultdict
import numpy as np
import pandas as pd


MIN_REWARD_PER_PROJECT = 1_000
MAX_REWARD_PER_PROJECT_PCT = .125

def scorer(ballots_data):
           
    budget_allocation = []
    category_scores = defaultdict(list)
    project_scores = defaultdict(lambda: defaultdict(list))
    for ballot in ballots_data:
        
        budget_allocation.append(ballot['budget'])
        assigned_category = ballot['category_assignment']

        for category_allocations in ballot['category_allocations']:
            category = list(category_allocations.keys())[0]
            category_percentage = float(list(category_allocations.values())[0])
            category_scores[category].append(category_percentage)

        for project_allocations in ballot['project_allocations']:
            project = list(project_allocations.keys())[0]
            project_percentage = list(project_allocations.values())[0]
            if pd.isnull(project_percentage):
                continue
            project_percentage = float(project_percentage)
            project_scores[assigned_category][project].append(project_percentage)    

    # Step 1A. Calculate total funding for the round based on median budget vote
    median_total_budget = np.median(budget_allocation)
    max_reward_per_project = median_total_budget * MAX_REWARD_PER_PROJECT_PCT
    print(f"\nMedian Budget: {median_total_budget:,.0f}")

    # Step 1B. Calculate medians for categories and normalize to weights across categories
    category_medians = {k: np.median(v)/100 for k, v in category_scores.items()}    
    category_total = sum(category_medians.values())
    category_weights = {k: v/category_total for k, v in category_medians.items()}

    # Step 2. Calculate medians for projects and normalize to weights within a category
    project_weights = defaultdict(lambda: defaultdict(list))
    for category, project_dict in project_scores.items():

        print("\nCategory:", category)
        print("-----------------")
        print(f"Median Allocation: {category_weights[category]*100:.3f}%")

        for project, scores in project_dict.items():
            project_weights[category][project] = np.median(scores) / 100
        category_subtotal = sum(project_weights[category].values())
        for k, v in project_weights[category].items():
            project_weights[category][k] = v/category_subtotal 

    # Step 3. Create an initial series of project funding allocations
    initial_project_allocations = pd.Series()
    for category, projects in project_weights.items():
        for project, score in projects.items():
            normalized_score = score * category_weights[category]
            initial_project_allocations.loc[project] = normalized_score * median_total_budget
    
    # Helper function to allocate funding
    def allocate_funding(project_scores, funding_balance):
        score_balance = project_scores.sum()
        allocations = pd.Series()
        
        for project, score in project_scores.sort_values(ascending=False).items():
            uncapped_funding_alloc = score / score_balance * funding_balance
            capped_funding_alloc = min(uncapped_funding_alloc, max_reward_per_project)
            allocations.loc[project] = capped_funding_alloc
            funding_balance -= capped_funding_alloc
            score_balance -= score

        return allocations
    
    # Step 4. Implement max cap and redistribute excess
    capped_allocations = allocate_funding(initial_project_allocations, median_total_budget)

    # Step 5. Set the funding for projects below the minimum cap to 0
    capped_allocations.loc[capped_allocations < MIN_REWARD_PER_PROJECT] = 0

    # Step 6. Allocate the remaining funding to projects below the maximum cap
    max_cap_funding = capped_allocations[capped_allocations == max_reward_per_project].sum()
    remaining_funding = median_total_budget - max_cap_funding
    remaining_projects = capped_allocations[capped_allocations < max_reward_per_project]
    capped_allocations.update(allocate_funding(remaining_projects, funding_balance=remaining_funding))

    # Return the capped allocations as a DataFrame
    results_dataframe = capped_allocations.copy().rename('rewards').reset_index()
    results_dataframe.rename(columns={'index': 'project_id'}, inplace=True)
    results_dataframe.set_index('project_id', inplace=True)

    return results_dataframe


def simulate_scorer(ballots_data, addresses):

    filtered_data = []
    for ballot in ballots_data:
        if ballot['voter_address'] in addresses:
            filtered_data.append(ballot)

    return scorer(filtered_data)
    
