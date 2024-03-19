import pandas as pd
import numpy as np
from datetime import datetime

# The Project Engagement Index measures the level of community engagement in different projects. It combines the number of unique contributors and the total amount of contributions to each project, providing insight into which projects are more actively engaging the community.

def calculate_engagement_index(df, level='project', weight_unique_contributors=0.7, weight_total_contributions=0.3):
    if level not in ['project', 'repo']:
        raise ValueError("Level must be 'project' or 'repo'")

    # Calculate the number of unique contributors per entity
    unique_contributors = df.groupby(level)['user'].nunique()

    # Calculate the total contributions per entity
    total_contributions = df.groupby(level)['total_amount'].sum()

    # Normalize the metrics
    max_unique_contributors = unique_contributors.max()
    max_total_contributions = total_contributions.max()
    normalized_unique_contributors = unique_contributors / max_unique_contributors
    normalized_total_contributions = total_contributions / max_total_contributions

    # Combine the two metrics into a single DataFrame
    scores = pd.DataFrame({
        'Unique Contributors': unique_contributors,
        'Total Contributions': total_contributions,
        'Normalized Unique Contributors': normalized_unique_contributors,
        'Normalized Total Contributions': normalized_total_contributions
    })

    # Calculate a weighted score
    scores['Engagement Index'] = (scores['Normalized Unique Contributors'] * weight_unique_contributors +
                                  scores['Normalized Total Contributions'] * weight_total_contributions)

    return scores.sort_values(by='Engagement Index', ascending=False)

# This function assesses the activity level of each repository by analyzing both the frequency and recency of contributions. It helps identify the most actively maintained or developed repositories, indicating current and ongoing community interest and involvement.

def calculate_activity_level(df, level='project', current_date='2023-11-01'):
    if level not in ['project', 'repo']:
        raise ValueError("Level must be 'project' or 'repo'")

    # Convert string dates to datetime objects
    df['month'] = pd.to_datetime(df['month'])

    # Calculate the frequency of contributions for each entity
    contribution_frequency = df.groupby(level)['total_amount'].sum()

    # Calculate recency scores for contributions
    latest_date = pd.to_datetime(current_date)
    df['recency_score'] = df['month'].apply(lambda date: 1 / (latest_date.year - date.year + 1))

    # Aggregate recency scores by entity
    recency_scores = df.groupby(level).apply(lambda x: np.sum(x['total_amount'] * x['recency_score']))

    # Combine the metrics into a single DataFrame
    scores = pd.DataFrame({
        'Contribution Frequency': contribution_frequency,
        'Recency Score': recency_scores
    })

    # Normalize the metrics
    max_frequency = scores['Contribution Frequency'].max()
    max_recency = scores['Recency Score'].max()
    scores['Normalized Frequency'] = scores['Contribution Frequency'] / max_frequency
    scores['Normalized Recency'] = scores['Recency Score'] / max_recency

    # Calculate an overall activity score (simple average of normalized scores)
    scores['Activity Level'] = (scores['Normalized Frequency'] + scores['Normalized Recency']) / 2

    return scores.sort_values(by='Activity Level', ascending=False)

# The Collaboration Index measures the degree of collaboration within a project or repository. It considers the potential collaborative interactions (pairs of users) and the diversity of collaborators, offering insight into the interconnectedness and collaborative nature of the contributor base.

def calculate_collaboration_index(df, level='project'):
    if level not in ['project', 'repo']:
        raise ValueError("Level must be 'project' or 'repo'")

    # Counting each pair of users per project or repository
    collaboration_pairs = df.groupby(level).apply(lambda x: len(x['user'].unique()) * (len(x['user'].unique()) - 1) / 2)
    
    # Count of unique users per project or repository
    unique_users = df.groupby(level)['user'].nunique()

    # Combine the metrics into a single DataFrame
    collaboration_scores = pd.DataFrame({
        'Collaboration Pairs': collaboration_pairs,
        'Unique Users': unique_users
    })

    # Normalize the metrics
    max_pairs = collaboration_scores['Collaboration Pairs'].max()
    max_users = collaboration_scores['Unique Users'].max()
    collaboration_scores['Normalized Pairs'] = collaboration_scores['Collaboration Pairs'] / max_pairs
    collaboration_scores['Normalized Users'] = collaboration_scores['Unique Users'] / max_users

    # Calculate an overall collaboration index (simple average of normalized scores)
    collaboration_scores['Collaboration Index'] = (collaboration_scores['Normalized Pairs'] + collaboration_scores['Normalized Users']) / 2

    return collaboration_scores.sort_values(by='Collaboration Index', ascending=False)

# This function calculates an Impact Factor for each project or repository by integrating various metrics, including total contributions, number of unique contributors, and activity levels. It aims to estimate the overall impact or significance of a project or repository within the community.

def calculate_impact_factor(df, level='project', current_date='2023-11-01'):
    if level not in ['project', 'repo']:
        raise ValueError("Level must be 'project' or 'repo'")

    # Convert string dates to datetime objects for recency calculation
    df['month'] = pd.to_datetime(df['month'])

    # Total Contributions
    total_contributions = df.groupby(level)['total_amount'].sum()

    # Number of Unique Contributors
    unique_contributors = df.groupby(level)['user'].nunique()

    # Activity Level - Frequency and Recency
    # Frequency
    contribution_frequency = df.groupby(level)['total_amount'].sum()

    # Recency
    latest_date = pd.to_datetime(current_date)
    df['recency_score'] = df['month'].apply(lambda date: 1 / (latest_date.year - date.year + 1))
    recency_scores = df.groupby(level).apply(lambda x: np.sum(x['total_amount'] * x['recency_score']))

    # Normalize the metrics
    max_total_contributions = total_contributions.max()
    max_unique_contributors = unique_contributors.max()
    max_frequency = contribution_frequency.max()
    max_recency = recency_scores.max()

    normalized_total_contributions = total_contributions / max_total_contributions
    normalized_unique_contributors = unique_contributors / max_unique_contributors
    normalized_frequency = contribution_frequency / max_frequency
    normalized_recency = recency_scores / max_recency

    # Combine the metrics into a single DataFrame
    impact_scores = pd.DataFrame({
        'Total Contributions': total_contributions,
        'Unique Contributors': unique_contributors,
        'Contribution Frequency': contribution_frequency,
        'Recency Score': recency_scores,
        'Normalized Total Contributions': normalized_total_contributions,
        'Normalized Unique Contributors': normalized_unique_contributors,
        'Normalized Frequency': normalized_frequency,
        'Normalized Recency': normalized_recency
    })

    # Calculate an overall impact score (simple average of normalized scores)
    impact_scores['Impact Factor'] = (impact_scores['Normalized Total Contributions'] +
                                      impact_scores['Normalized Unique Contributors'] +
                                      impact_scores['Normalized Frequency'] +
                                      impact_scores['Normalized Recency']) / 4

    return impact_scores.sort_values(by='Impact Factor', ascending=False)

# The User Diversity Score evaluates the diversity of contributors to a project or repository. It calculates a diversity index based on the variety of unique user IDs contributing, highlighting projects or repositories with a broader range of contributors.

def calculate_user_diversity_score(df, level='project'):
    if level not in ['project', 'repo']:
        raise ValueError("Level must be 'project' or 'repo'")

    # Count of unique users contributing to each project or repository
    unique_users = df.groupby(level)['user'].nunique()

    # Calculate the total number of contributions for normalization
    total_contributions = df.groupby(level)['total_amount'].sum()

    # Normalize the unique user count
    diversity_scores = unique_users / total_contributions

    # Combine into a DataFrame
    diversity_scores_df = pd.DataFrame({
        'Unique Users': unique_users,
        'Total Contributions': total_contributions,
        'Diversity Score': diversity_scores
    })

    return diversity_scores_df.sort_values(by='Diversity Score', ascending=False)