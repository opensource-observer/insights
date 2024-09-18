# Optimism Retro Funding 5

## Summary

This directory includes several analysis notebooks for Optimism Retro Funding 5.

1. `RF5_GitHub_RepoMetrics.ipynb`: Analysis of project GitHub metrics such as contributors, stars, forks, and trust scores (powered by OSO and [OpenRank](https://openrank.com/)). Export of the results can be found [here](./data/rf5_applicant_github_metrics.csv).
2. `RF5_SyntheticVoter.ipynb`: Generate random voters based on RF5-specific round parameters. Creates a JSON file in the `data` directory, which can be used to run round simulations with `RF5_ResultsCalculator.ipynb` and test scoring approaches.
3. `RF5_GitHub_RepoMetrics_Simulation.ipynb` and `RF5_GitHub_Metrics_Simulation.ipynb`: Pre-round data simulation of project GitHub metrics, based on past applicants. One version shows the data for a single repo, while the other shows the simulation for all repos owned by a project.

## Project GitHub Metrics

The following fields are included in the metrics analysis for Retro Funding 5:

1. `project_name`: Name of the project.
2. `project_category_id`: Category ID of the project (1, 2, 3).
3. `repo(s)`: Repository URLs associated with the project based on the application.
4. `trust_rank_for_repo_in_category`: Ranking of the repository's OpenRank trust score within its category. A score of 1 indicates the highest ranking repo in its category.
5. `num_contributors`: Total number of contributors before August 1, 2024. A contributor is defined as any non-bot user that has contributed to the repository (since 2015) by committing code directly to a repository, opening an issue, or opening/reviewing a pull request.
6. `num_trusted_contributors`: Number of trusted contributors before August 1, 2024. A subset of the contributors defined above, this is the number of contributors that are also in the top 420 of the [OpenRank](https://openrank.com/) developer trust score.
7. `num_contributors_last_6_months`: Number of contributors over the period Feburary 1, 2024 - August 1, 2024.
8. `num_stars`: Total number of stars as of September 16, 2024.
9. `num_trusted_stars`: Number of stars from trusted users before August 1, 2024. A subset of the stars defined above, this is the number of stars from users that are also in the top 420 of the [OpenRank](https://openrank.com/) developer trust score.
10. `trust_weighted_stars`: This metric is a percentage score between 0% and 100%, representing the sum of the reputation share of the developers who starred the repo.  If all developers in OpenRank developer ranking have starred a particular repo, the metric's value is going to be 100% for this particular repo. The more and the higher ranked developer who starred the repo, the higher the percentage value, the higher impact and quality of this repo. We calculate this metric by first calculating every developer's reputation share (%) based on their OpenRank score, then sum them up if they starred the target repo.
11. `num_forks`: Total number of forks as of September 16, 2024.
12. `num_trusted_forks`: Number of forks from trusted users before August 1, 2024. A subset of the forks defined above, this is the number of forks from users that are also in the top 420 of the [OpenRank](https://openrank.com/) developer trust score.
13. `trust_weighted_forks`: This metric is a percentage score between 0% and 100%, representing the sum of the reputation share of the developers who forked the repo. If all developers in OpenRank developer ranking have forked a particular repo, the metric's value is going to be 100% for this particular repo. The more and the higher ranked developer who forked the target repo, the higher the percentage value, the higher impact and quality of this repo. We calculate this metric by first calculating every developer's reputation share (%) based on their OpenRank score, then sum them up if they forked the target repo.
14. `age_of_project_years`: Age of the project in years, measured from the project's first public commit to August 1, 2024.
15. `license(s)`: License(s) used by the project.
