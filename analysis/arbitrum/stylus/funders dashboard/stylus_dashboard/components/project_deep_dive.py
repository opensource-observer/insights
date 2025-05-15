import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
from ..config import DATA_PATHS
from ..utils.data_processing import load_data

def render_project_deep_dive():
    """Render the project deep dive analysis tab content."""
    st.header("Project Deep Dive Analysis")
    st.markdown("""
    This page provides a comprehensive analysis of individual projects, including development velocity metrics, 
    community health indicators, and project growth statistics. Select a project to view detailed metrics 
    such as commit frequency, contributor activity, and repository-level developer engagement.
    """)
    
    # Load data
    df = load_data(DATA_PATHS["stylus_metrics"])
    repo_devs_df = load_data(DATA_PATHS["active_devs_by_repo"])
    project_attributes = pd.read_csv(DATA_PATHS["project_attributes"])
    
    # Project selection
    all_projects = df['display_name'].unique()
    selected_project = st.selectbox(
        "Select Project for Deep Dive",
        all_projects
    )
    
    # Calculate date 180 days ago
    latest_date = df['sample_date'].max()
    ninety_days_ago = latest_date - timedelta(days=180)
    
    # Filter data for selected project and last 90 days
    project_data = df[
        (df['display_name'] == selected_project) &
        (df['sample_date'] >= ninety_days_ago)
    ]
    
    # Get the project_name from project_data
    project_name = project_data['project_name'].iloc[0] if not project_data.empty else None
    
    # Get project attributes
    project_attr = project_attributes[project_attributes['project_name'] == project_name]
    if not project_attr.empty:
        st.subheader("Project Attributes")
        
        # Create a more compact layout using badges
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("**Onchain Status**", help="Does the project write to or read from the blockchain?")
            st.markdown(f"`{project_attr['onchain_status'].iloc[0]}`")
        
        with col2:
            st.markdown("**Stylus Usage**", help="Contract logic or computation on Stylus (Direct)")
            st.markdown(f"`{project_attr['stylus_usage'].iloc[0]}`")
        
        with col3:
            st.markdown("**Origin**", help="Project with working product on other chains expanding support to Stylus (Established) versus project was conceived specifically for Arbitrum Stylus (Stylus-Native)")
            st.markdown(f"`{project_attr['origin'].iloc[0]}`")
        
        with col4:
            st.markdown("**Categories**", help="Project Type / Primary Function")
            categories = [cat.strip() for cat in project_attr['categories'].iloc[0].split(',')]
            st.markdown(" ".join([f"`{cat}`" for cat in categories]))
    
    # Filter repository-level data for selected project
    project_repo_data = repo_devs_df[
        (repo_devs_df['project_name'] == project_name) &
        (repo_devs_df['sample_date'] >= ninety_days_ago) &
        (repo_devs_df['metric_name'] == 'GITHUB_active_developers_monthly')
    ]

    # Create three columns for metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Development Velocity")
        
        # Weekly commits
        weekly_commits = project_data[project_data['metric_name'] == 'GITHUB_commits_weekly']
        if not weekly_commits.empty:
            fig = px.bar(
                weekly_commits,
                x='sample_date',
                y='amount',
                title='Weekly Commits'
            )
            fig.update_yaxes(range=[0, weekly_commits['amount'].max() * 1.1])
            st.plotly_chart(fig, use_container_width=True)
        
        # Weekly merged PRs
        merged_prs = project_data[project_data['metric_name'] == 'GITHUB_merged_pull_requests_weekly']
        if not merged_prs.empty:
            st.metric(
                "Average Weekly Merged PRs",
                f"{merged_prs['amount'].mean():.1f}"
            )
    
    with col2:
        st.subheader("Community Health")
        
        # New vs returning contributors
        new_contributors = project_data[project_data['metric_name'] == 'GITHUB_new_contributors_monthly']
        active_contributors = project_data[project_data['metric_name'] == 'GITHUB_active_contributors_monthly']
        
        if not new_contributors.empty and not active_contributors.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=new_contributors['sample_date'],
                y=new_contributors['amount'],
                name='New Contributors'
            ))
            fig.add_trace(go.Bar(
                x=active_contributors['sample_date'],
                y=active_contributors['amount'],
                name='Active Contributors'
            ))
            max_value = max(new_contributors['amount'].max(), active_contributors['amount'].max())
            fig.update_layout(
                title='Contributor Growth',
                barmode='group',
                yaxis=dict(range=[0, max_value * 1.1])
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Full-time vs part-time ratio
        full_time = project_data[project_data['metric_name'] == 'GITHUB_full_time_developers_monthly']
        part_time = project_data[project_data['metric_name'] == 'GITHUB_part_time_developers_monthly']
        
        if not full_time.empty and not part_time.empty:
            ratio = full_time['amount'].iloc[-1] / (full_time['amount'].iloc[-1] + part_time['amount'].iloc[-1])
            st.metric(
                "Full-time Developer Ratio",
                f"{ratio:.1%}"
            )
    
    with col3:
        st.subheader("Project Growth")
        
        # Forks trend
        forks = project_data[project_data['metric_name'] == 'GITHUB_forks_monthly']
        if not forks.empty:
            fig = px.bar(
                forks,
                x='sample_date',
                y='amount',
                title='Monthly Forks'
            )
            fig.update_yaxes(range=[0, forks['amount'].max() * 1.1])
            st.plotly_chart(fig, use_container_width=True)
        
        # Stars trend
        stars = project_data[project_data['metric_name'] == 'GITHUB_stars_monthly']
        if not stars.empty:
            st.metric(
                "Total Stars",
                f"{stars['amount'].sum():,.0f}"
            ) 

    # Repository-level active developers
    if not project_repo_data.empty:
        # Create a pivot table with repositories as rows and months as columns
        pivot_table = project_repo_data.pivot_table(
            index='artifact_name',
            columns='sample_date',
            values='amount',
            aggfunc='sum'
        ).fillna(0)  # Fill NaN values with 0
        
        # Format the column names to show just the month and year
        pivot_table.columns = [col.strftime('%b %Y') for col in pivot_table.columns]
        
        # Sort by total active developers across all months
        pivot_table['total'] = pivot_table.sum(axis=1)
        pivot_table = pivot_table.sort_values('total', ascending=True)
        pivot_table = pivot_table.drop('total', axis=1)  # Remove the total column after sorting
        
        st.subheader("Monthly Active Developers by Repository")
        st.markdown("""
        This heatmap shows the number of active developers contributing to each repository over time. 
        """)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale='Viridis',
            hoverongaps=False,
            text=pivot_table.values,
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate="Repository: %{y}<br>Month: %{x}<br>Active Developers: %{z}<extra></extra>"
        ))
        
        fig.update_layout(
            title="Active Developers Heatmap",
            xaxis_title="Month",
            yaxis_title="Repository",
            height=max(400, len(pivot_table) * 30),  # Adjust height based on number of repositories
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)