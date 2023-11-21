# GitHub Contributions Analysis Toolkit

This toolkit provides a set of Python functions to analyze GitHub contribution data. It is designed to offer insights into various aspects of GitHub projects and users, including project engagement, activity levels, collaboration, user contributions, and overall impact.

## Project Scoring Functions

1. **calculate_engagement_index**: Measures the engagement level of projects or repositories.
2. **calculate_activity_level**: Calculates the activity level of projects or repositories.
3. **calculate_collaboration_index**: Estimates the degree of collaboration within projects or repositories.
4. **calculate_impact_factor**: Evaluates the overall impact of projects or repositories.

### 1. calculate_engagement_index
- **Purpose**: Evaluates the engagement level of projects or repositories.
- **Parameters**:
  - `df` (DataFrame): Dataset containing GitHub contributions.
  - `level` (str): 'project' or 'repo'.
  - `weight_unique_contributors`, `weight_total_contributions` (float): Weights for contributors and contributions.
- **How it Works**: Counts unique contributors and sums total contributions, then normalizes and combines these values into an engagement index.

### 2. calculate_activity_level
- **Purpose**: Measures the activity level of projects or repositories.
- **Parameters**:
  - `df` (DataFrame): Dataset.
  - `level` (str): 'project' or 'repo'.
  - `current_date` (str): Date for recency calculation.
- **How it Works**: Calculates contribution frequency and recency, normalizes these metrics, and averages them to determine activity level.

### 3. calculate_collaboration_index
- **Purpose**: Assesses collaboration within projects or repositories.
- **Parameters**:
  - `df` (DataFrame): Dataset.
  - `level` (str): 'project' or 'repo'.
- **How it Works**: Calculates potential collaborative pairs and unique users, normalizes and averages these metrics to compute the collaboration index.

### 4. calculate_impact_factor
- **Purpose**: Evaluates the overall impact of projects or repositories.
- **Parameters**:
  - `df` (DataFrame): Dataset.
  - `level` (str): 'project' or 'repo'.
  - `current_date` (str): Date for recency calculation.
- **How it Works**: Combines contributions, unique contributors, frequency, and recency, normalizes and averages these to determine impact factor.

## User Scoring Functions

1. **calculate_user_contribution_score**: Calculates a score for each user based on their total contributions and the diversity of repositories they have contributed to.
2. **calculate_user_diversity_index**: Measures the diversity of a user's contributions across different projects or repositories.
3. **calculate_user_influence_score**: Estimates a user's influence based on the impact of the projects or repositories they contribute to.
4. **calculate_user_consistency_score**: Evaluates the consistency of a user's contributions over time.
5. **calculate_user_collaboration_index**: Measures a user’s involvement in collaborative projects or repositories.

## User Scoring Functions

### 1. calculate_user_contribution_score
- **Purpose**: Calculates a score for each user based on their total contributions and the diversity of repositories they have contributed to.
- **Parameters**:
  - `df` (DataFrame): The dataset containing GitHub contributions.
- **How it Works**: The function calculates total contributions and counts the unique projects and repositories contributed to by each user. These values are then normalized and combined into a single contribution score.

### 2. calculate_user_diversity_index
- **Purpose**: Measures the diversity of a user's contributions across different projects or repositories.
- **Parameters**:
  - `df` (DataFrame): The dataset.
- **How it Works**: This function counts the number of unique projects and repositories each user has contributed to and the total contributions. The unique counts are normalized and combined to create a diversity index.

### 3. calculate_user_influence_score
- **Purpose**: Estimates a user's influence based on the impact of the projects or repositories they contribute to.
- **Parameters**:
  - `df` (DataFrame): The dataset.
  - `impact_scores` (DataFrame): Impact scores for projects or repositories.
- **How it Works**: The function merges user contribution data with project or repository impact scores and calculates a weighted average impact for each user. It also considers the diversity of the user's contributions in computing the influence score.

### 4. calculate_user_consistency_score
- **Purpose**: Evaluates the consistency of a user's contributions over time.
- **Parameters**:
  - `df` (DataFrame): The dataset.
- **How it Works**: Contributions per month are calculated for each user, and the standard deviation of these contributions is determined. The consistency score is then adjusted based on total contributions and the calculated standard deviation.

### 5. calculate_user_collaboration_index
- **Purpose**: Measures a user’s involvement in collaborative projects or repositories.
- **Parameters**:
  - `df` (DataFrame): The dataset.
- **How it Works**: The function identifies pairs of users who have collaborated on the same project, counts the unique collaborators for each user, and then normalizes these counts to compute a collaboration index.

## Usage Example

For project scoring functions:
```python
from scoring_tools.project_scores import calculate_impact_factor
df = pd.read_csv('path/to/github_graph.csv')
project_impact_factors = calculate_impact_factor(df, level='project')
print(project_impact_factors)
```

For user scoring functions:
```python
from scoring_tools.user_scores import calculate_user_contribution_score
df = pd.read_csv('path/to/github_graph.csv')
user_contribution_scores = calculate_user_contribution_score(df)
print(user_contribution_scores)
```

Replace the function names with the desired function from the respective lists above and adjust parameters as needed.

## Conclusion

This toolkit offers a comprehensive approach to analyze GitHub contribution data, providing key insights into project and user activities, contributions, collaborations, and impacts. These functions are flexible and can be adapted to specific analytical needs.








