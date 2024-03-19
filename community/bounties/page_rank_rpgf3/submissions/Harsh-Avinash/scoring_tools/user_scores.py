import pandas as pd
import numpy as np
from project_scores import calculate_impact_factor
import itertools

# This function calculates a score for each user based on their total contributions to projects and the diversity of repositories they have contributed to. It aims to identify key contributors by considering both the volume and range of their contributions.

def calculate_user_contribution_score(df):
    # Calculate total contributions per user
    total_contributions = df.groupby('user')['total_amount'].sum()

    # Calculate the number of unique projects and repositories contributed to by each user
    unique_projects = df.groupby('user')['project'].nunique()
    unique_repositories = df.groupby('user')['repo'].nunique()

    # Normalize these values
    max_total_contributions = total_contributions.max()
    max_unique_projects = unique_projects.max()
    max_unique_repositories = unique_repositories.max()

    normalized_total_contributions = total_contributions / max_total_contributions
    normalized_unique_projects = unique_projects / max_unique_projects
    normalized_unique_repositories = unique_repositories / max_unique_repositories

    # Combine these metrics into a single DataFrame
    user_scores = pd.DataFrame({
        'Total Contributions': total_contributions,
        'Unique Projects': unique_projects,
        'Unique Repositories': unique_repositories,
        'Normalized Total Contributions': normalized_total_contributions,
        'Normalized Unique Projects': normalized_unique_projects,
        'Normalized Unique Repositories': normalized_unique_repositories
    })

    # Calculate a combined contribution score
    # The formula here is a simple average of the normalized scores
    user_scores['Contribution Score'] = (user_scores['Normalized Total Contributions'] + 
                                         user_scores['Normalized Unique Projects'] + 
                                         user_scores['Normalized Unique Repositories']) / 3

    return user_scores.sort_values(by='Contribution Score', ascending=False)

# Measure the diversity of a user's contributions across different projects or repositories.

def calculate_user_diversity_index(df):
    # Count of unique projects/repositories contributed to by each user
    unique_projects_per_user = df.groupby('user')['project'].nunique()
    unique_repos_per_user = df.groupby('user')['repo'].nunique()

    # Total contributions per user
    total_contributions_per_user = df.groupby('user')['total_amount'].sum()

    # Calculate the diversity index
    user_diversity_scores = pd.DataFrame({
        'Unique Projects': unique_projects_per_user,
        'Unique Repositories': unique_repos_per_user,
        'Total Contributions': total_contributions_per_user
    })

    # Normalize the counts
    max_unique_projects = unique_projects_per_user.max()
    max_unique_repos = unique_repos_per_user.max()

    user_diversity_scores['Normalized Project Diversity'] = user_diversity_scores['Unique Projects'] / max_unique_projects
    user_diversity_scores['Normalized Repository Diversity'] = user_diversity_scores['Unique Repositories'] / max_unique_repos

    # Calculate a combined diversity score
    user_diversity_scores['Diversity Index'] = (user_diversity_scores['Normalized Project Diversity'] + 
                                                user_diversity_scores['Normalized Repository Diversity']) / 2

    return user_diversity_scores.sort_values(by='Diversity Index', ascending=False)

# Estimate a user's influence based on the impact of the projects or repositories they contribute to.

def calculate_user_influence_score(df, impact_scores):
    # Merge the original dataframe with the impact scores
    df_merged = df.merge(impact_scores[['Impact Factor']], left_on='project', right_index=True)

    # Calculate the weighted average impact for each user
    def weighted_avg(x):
        if x['total_amount'].sum() == 0:
            return 0
        return np.average(x['Impact Factor'], weights=x['total_amount'])

    average_impact_per_user = df_merged.groupby('user').apply(weighted_avg)

    # Calculate the diversity of a user's contributions (number of unique projects contributed to)
    user_project_diversity = df.groupby('user')['project'].nunique()

    # Combine into a DataFrame
    user_influence_scores = pd.DataFrame({
        'Average Project Impact': average_impact_per_user,
        'Project Diversity': user_project_diversity,
        'Total Contributions': df.groupby('user')['total_amount'].sum(),
    })

    # Incorporating diversity into the influence score
    max_avg_impact = user_influence_scores['Average Project Impact'].max()
    max_diversity = user_influence_scores['Project Diversity'].max()
    user_influence_scores['Influence Score'] = (user_influence_scores['Average Project Impact'] / max_avg_impact) * \
                                               (user_influence_scores['Project Diversity'] / max_diversity)

    return user_influence_scores.sort_values(by='Influence Score', ascending=False)

# Evaluate the consistency of a user's contributions over time.

def calculate_user_consistency_score(df):
    # Convert the month to a datetime for proper grouping
    df['month'] = pd.to_datetime(df['month'])

    # Group by user and month, then count contributions
    contributions_per_month = df.groupby(['user', df['month'].dt.to_period('M')])['total_amount'].sum()

    # Calculate the standard deviation of contributions for each user
    std_dev_contributions = contributions_per_month.groupby('user').std()

    # Total contributions per user
    total_contributions = df.groupby('user')['total_amount'].sum()

    # Adjusted consistency score (considering both std deviation and total contributions)
    # Adding a small value to std deviation to avoid division by zero for users with consistent contributions
    adjusted_consistency_scores = total_contributions / (std_dev_contributions + 1e-6)

    # Normalize the adjusted consistency scores
    max_score = adjusted_consistency_scores.max()
    normalized_consistency_scores = adjusted_consistency_scores / max_score

    # Combine into a DataFrame
    user_consistency_scores = pd.DataFrame({
        'Standard Deviation': std_dev_contributions,
        'Total Contributions': total_contributions,
        'Adjusted Consistency Score': adjusted_consistency_scores,
        'Normalized Consistency Score': normalized_consistency_scores
    })

    return user_consistency_scores.sort_values(by='Normalized Consistency Score', ascending=False)

#  Measure a user’s involvement in collaborative projects or repositories.

def calculate_user_collaboration_index(df):
    # Create a DataFrame where each row represents a pair of users who contributed to the same project
    collaboration_pairs = df.groupby('project').apply(lambda x: pd.DataFrame(list(itertools.combinations(x['user'].unique(), 2))))

    # Flatten the resulting DataFrame
    collaboration_pairs = collaboration_pairs.reset_index(level=0, drop=True)
    collaboration_pairs.columns = ['User1', 'User2']

    # Count unique collaborators for each user
    unique_collaborators_user1 = collaboration_pairs.groupby('User1')['User2'].nunique()
    unique_collaborators_user2 = collaboration_pairs.groupby('User2')['User1'].nunique()

    # Combine the counts for each user
    total_unique_collaborators = unique_collaborators_user1.add(unique_collaborators_user2, fill_value=0)

    # Normalize the scores
    max_collaborators = total_unique_collaborators.max()
    normalized_collaboration_index = total_unique_collaborators / max_collaborators

    # Combine into a DataFrame
    user_collaboration_index = pd.DataFrame({
        'Total Unique Collaborators': total_unique_collaborators,
        'Collaboration Index': normalized_collaboration_index
    })

    return user_collaboration_index.sort_values(by='Collaboration Index', ascending=False)
