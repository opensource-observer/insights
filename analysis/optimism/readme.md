# Optimism Insights and Data Science

## Introduction

Insights and data science for measuring the growth of open source software contributions to the Optimism ecosystem. The goal of these insights is to improve the ROI and governance of grant programs.

This directory contains our analysis and data science work, mostly in the form of Jupyter notebooks and scripts to facilitate ad hoc analysis.

### Retro Funding 6 (in progress)

This directory includes our work with Metrics Garden Labs on qualitative impact metrics. We've written indexers for various EAS attestation schemas and linked them to governance members (i.e., delegates and badgeholders). We created synthetic data to test the indexers and the data pipeline, and serve dummy metrics to the frontend. We worked with the Foundation and Agora to implement 8 attestation-based impact metrics for the Retro Funding 6 cohort.

Key contributions include:

- `eas.py`: Modules for indexing EAS attestation schemas and fetching relevant metadata linked to attestations.
- `RF6_ImpactAttestations_MockMetrics.ipynb`: Mock data generation for the 8 attestation-based impact metrics, which references real projects and delegates / citizens (identified from attestations and OP Atlas).

### Retro Funding 5

This directory includes a variety of analysis notebooks for Retro Funding 5, as well as static impact metrics for the OSS projects in the round. We also worked with the OP Labs data team to test various scoring implementations for the round and audit preliminary data.

Key contributions include:

- `RF5_GitHub_RepoMetrics.ipynb`: Analysis of project GitHub metrics such as contributors, stars, forks, and trust scores (powered by OSO and [OpenRank](https://openrank.com/)). Export of the results can be found [here](./data/rf5_applicant_github_metrics.csv).
- `RF5_SyntheticVoter.ipynb`: Generate random voters based on RF5-specific round parameters. Creates a JSON file in the `data` directory, which can be used to run round simulations with `RF5_ResultsCalculator.ipynb` and test scoring approaches.
- `RF5_GitHub_RepoMetrics_Simulation.ipynb` and `RF5_GitHub_Metrics_Simulation.ipynb`: Pre-round data simulation of project GitHub metrics, based on past applicants. One version shows the data for a single repo, while the other shows the simulation for all repos owned by a project.
- `RF5_ResultsCalculator_Testing.ipynb` and `RF5_ResultsCalculator_Production.ipynb`: Calculate the results of the round based on the scoring approach. The testing version is used to test the scoring approach with synthetic data, while the main version is used to audit the results for the round.

### Retro Funding 4

In addition to developing the onchain impact metrics for the round, we helped the Foundation perform extensive eligibility checks on the applicants and verify open source licenses. We were onhand for a month to help applicants and reviewers answer questions about the round mechanics and verify their data. We also worked with Agora and the OP Labs data team to test various scoring implementations for the round and audit calculations. Finally, we published an in-depth report on revealed preferences of voters based on the round results.

Key contributions include:

- `RF4_LicenseChecker.ipynb`: Check the licenses of the projects in the round and verify that they are open source.
- `rf4_calcs_audit.py`: Audit the calculations for the round and verify the results.
- `RF4_BallotBox.ipynb`: Post round analysis of the results and revealed preferences of voters.
- `data/op_rf4_contracts_by_project.parquet`: Parquet file of all contracts linked to projects in the round.

### Other

We conducted longitudinal analysis of various retro funding cohorts (`longitudinal/20240714_RetroFunding_LongitudinalAnalysis.ipynb`), as well as round-specific analysis for Retro Funding 3 (`retropgf3/`) and RetroPGF2 (`retropgf2/`).