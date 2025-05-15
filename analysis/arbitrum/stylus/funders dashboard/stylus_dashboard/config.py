import streamlit as st

# Page configuration
PAGE_CONFIG = {
    "page_title": "Stylus Sprint Ecosystem Dashboard",
    "page_icon": "📊",
    "layout": "wide"
}

# Time window options
TIME_WINDOWS = {
    "Last 3 Months": 90,
    "Last 6 Months": 180,
    "Last 9 Months": 270,
    "Last 12 Months": 365,
    "Last 36 Months": 1095
}

# Available metrics for analysis
AVAILABLE_METRICS = {
    'GITHUB_active_developers_monthly': 'Active Developers',
    'GITHUB_commits_monthly': 'Commits',
    'GITHUB_closed_issues_monthly': 'Closed Issues',
    'GITHUB_merged_pull_requests_monthly': 'Merged PRs',        
    'GITHUB_stars_monthly': 'Stars',
    'GITHUB_forks_monthly': 'Forks'
}

# Risk assessment thresholds
RISK_THRESHOLDS = {
    "active_devs_threshold": 10.0,
    "new_contributors_threshold": 20.0,
    "pr_merge_time_threshold": 20.0,
    "issue_backlog_threshold": 1.5
}

# Data file paths
DATA_PATHS = {
    "project_orgs": "./data/project_orgs.csv",
    "project_applications": "./data/project_applications.csv",
    "arb_projects": "./data/arb_projects_active_dev_monthly.csv",
    "stylus_metrics": "./data/stylus_github_metrics.csv",
    "dependencies": "./data/stylus_dependencies_active_dev_monthly.csv",
    "sdk_dependencies": "./data/stylus-sdk-rs-dependencies.csv",
    "active_devs_by_repo": "./data/stylus_github_metrics_repo.csv",
    "downstream_dependencies": "./data/project_dependencies.csv",
    "project_attributes": "./data/project_attributes.csv"
} 