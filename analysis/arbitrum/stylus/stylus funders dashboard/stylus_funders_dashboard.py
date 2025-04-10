import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import plotly.express as px
import networkx as nx

# Set page configuration
st.set_page_config(
    page_title="Stylus Funders Dashboard",
    page_icon="📊",
    layout="wide"
)

# Main title
st.title("📊 Stylus Funders Dashboard")

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Project Activity", "Project Deep Dive", "Risk Assessment", "Network Analysis"])

# Tab 1: Overview
with tab1:
    st.header("Overview")
    st.markdown("""
    ### Combined Developer Activity
    This dashboard shows the combined developer activity across all projects in the Stylus Sprint. 
    The metrics below represent the total contributions from all participating projects, giving you a comprehensive 
    view of the ecosystem's growth and engagement over time.
    """)

    # Read file
    df = pd.read_csv('stylus_github_metrics.csv')
    
    # Convert date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Get the latest date in the dataset
    latest_date = df['Date'].max()
    
    # Calculate date one year ago
    one_year_ago = latest_date - timedelta(days=365)
    
    # Filter data for the last year
    df = df[df['Date'] >= one_year_ago]
    
    # Aggregate data across all projects
    # Group by Date and Metric, then sum the values
    aggregated_df = df.groupby(['Date', 'Metric'])['Value'].sum().reset_index()
    
    # Create subplot figure
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Monthly Commits',
            'Monthly Closed Issues',
            'Monthly Merged Pull Requests',
            'Monthly Active Developers'
        )
    )
    
    # Add traces for each metric
    metrics = {
        'GITHUB_commits_monthly': (1, 1),
        'GITHUB_closed_issues_monthly': (1, 2),
        'GITHUB_merged_pull_requests_monthly': (2, 1),
        'GITHUB_active_developers_monthly': (2, 2)
    }
    
    for metric, (row, col) in metrics.items():
        metric_df = aggregated_df[aggregated_df['Metric'] == metric]
        fig.add_trace(
            go.Scatter(
                x=metric_df['Date'],
                y=metric_df['Value'],
                name=metric.replace('GITHUB_', '').replace('_', ' ').title()
            ),
            row=row, col=col
        )
    
    # Update layout
    fig.update_layout(
        height=800,
        showlegend=False,
        title_text=f"GitHub Activity Metrics - All Projects (Last 12 Months: {one_year_ago.strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d')})",
        title_x=0.5
    )
    
    # Update y-axes labels
    fig.update_yaxes(title_text="Total Count", row=1, col=1)
    fig.update_yaxes(title_text="Total Count", row=1, col=2)
    fig.update_yaxes(title_text="Total Count", row=2, col=1)
    fig.update_yaxes(title_text="Total Count", row=2, col=2)
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True)

# Tab 2: Project Activity
with tab2:
    st.header("Project Activity Analysis")
    
    # Metric selection with radio buttons
    available_metrics = {
        'GITHUB_commits_monthly': 'Commits',
        'GITHUB_closed_issues_monthly': 'Closed Issues',
        'GITHUB_merged_pull_requests_monthly': 'Merged PRs',
        'GITHUB_active_developers_monthly': 'Active Developers',
        'GITHUB_stars_monthly': 'Stars',
        'GITHUB_forks_monthly': 'Forks'
    }
    
    selected_metric = st.radio(
        "Select Metric for Heatmap",
        options=list(available_metrics.keys()),
        format_func=lambda x: available_metrics[x],
        horizontal=True
    )
    
    # Filter data for selected metric
    heatmap_data = df[df['Metric'] == selected_metric]
    
    # Aggregate data to handle duplicates
    heatmap_data = heatmap_data.groupby(['Name', 'Date'])['Value'].sum().reset_index()
    
    # Pivot data for heatmap
    heatmap_pivot = heatmap_data.pivot(
        index='Name',
        columns='Date',
        values='Value'
    )
    
    # Create heatmap
    fig = px.imshow(
        heatmap_pivot,
        labels=dict(
            x="Date",
            y="Project",
            color=available_metrics[selected_metric]
        ),
        aspect="auto",
        color_continuous_scale="Viridis"
    )
    
    # Update layout
    fig.update_layout(
        title=f"Project Activity Heatmap - {available_metrics[selected_metric]}",
        height=600,
        xaxis_title="Date",
        yaxis_title="Project"
    )
    
    # Display the heatmap
    st.plotly_chart(fig, use_container_width=True)

# Tab 3: Project Deep Dive
with tab3:
    st.header("Project Deep Dive Analysis")
    
    # Project selection
    all_projects = df['Name'].unique()
    selected_project = st.selectbox(
        "Select Project for Deep Dive",
        all_projects
    )
    
    # Calculate date 180 days ago
    latest_date = df['Date'].max()
    ninety_days_ago = latest_date - timedelta(days=180)
    
    # Filter data for selected project and last 90 days
    project_data = df[
        (df['Name'] == selected_project) &
        (df['Date'] >= ninety_days_ago)
    ]
    
    # Create three columns for metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Development Velocity")
        
        # Weekly commits
        weekly_commits = project_data[project_data['Metric'] == 'GITHUB_commits_weekly']
        if not weekly_commits.empty:
            fig = px.bar(
                weekly_commits,
                x='Date',
                y='Value',
                title='Weekly Commits'
            )
            fig.update_yaxes(range=[0, weekly_commits['Value'].max() * 1.1])
            st.plotly_chart(fig, use_container_width=True)
        
        # PR merge time
        pr_merge_time = project_data[project_data['Metric'] == 'GITHUB_avg_prs_time_to_merge_quarterly']
        if not pr_merge_time.empty:
            st.metric(
                "Average PR Merge Time",
                f"{pr_merge_time['Value'].iloc[-1]:.1f} days"
            )
    
    with col2:
        st.subheader("Community Health")
        
        # New vs returning contributors
        new_contributors = project_data[project_data['Metric'] == 'GITHUB_new_contributors_monthly']
        active_contributors = project_data[project_data['Metric'] == 'GITHUB_active_contributors_monthly']
        
        if not new_contributors.empty and not active_contributors.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=new_contributors['Date'],
                y=new_contributors['Value'],
                name='New Contributors'
            ))
            fig.add_trace(go.Bar(
                x=active_contributors['Date'],
                y=active_contributors['Value'],
                name='Active Contributors'
            ))
            max_value = max(new_contributors['Value'].max(), active_contributors['Value'].max())
            fig.update_layout(
                title='Contributor Growth',
                barmode='group',
                yaxis=dict(range=[0, max_value * 1.1])
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Full-time vs part-time ratio
        full_time = project_data[project_data['Metric'] == 'GITHUB_full_time_developers_monthly']
        part_time = project_data[project_data['Metric'] == 'GITHUB_part_time_developers_monthly']
        
        if not full_time.empty and not part_time.empty:
            ratio = full_time['Value'].iloc[-1] / (full_time['Value'].iloc[-1] + part_time['Value'].iloc[-1])
            st.metric(
                "Full-time Developer Ratio",
                f"{ratio:.1%}"
            )
    
    with col3:
        st.subheader("Project Growth")
        
        # Forks trend
        forks = project_data[project_data['Metric'] == 'GITHUB_forks_monthly']
        if not forks.empty:
            fig = px.bar(
                forks,
                x='Date',
                y='Value',
                title='Monthly Forks'
            )
            fig.update_yaxes(range=[0, forks['Value'].max() * 1.1])
            st.plotly_chart(fig, use_container_width=True)
        
        # Stars trend
        stars = project_data[project_data['Metric'] == 'GITHUB_stars_monthly']
        if not stars.empty:
            st.metric(
                "Total Stars",
                f"{stars['Value'].sum():,.0f}"
            )
    

# Tab 4: Risk Assessment
with tab4:
    st.header("Risk Assessment & Early Warning System")
    st.markdown("""
    ### Project Health Indicators
    This dashboard tracks key metrics that serve as early warning indicators for project health.
    Alerts are triggered when metrics show concerning trends over the last 3 months.
    """)
    
    # Calculate date 120 days ago for trend analysis
    latest_date = df['Date'].max()
    days_ago = latest_date - timedelta(days=120)
    
    # Project selection
    all_projects = df['Name'].unique()
    selected_project = st.selectbox(
        "Select Project for Risk Assessment",
        all_projects
    )
    
    # Filter data for selected project and last 90 days
    project_data = df[
        (df['Name'] == selected_project) &
        (df['Date'] >= days_ago)
    ]
    
    # Create columns for metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Contributor Engagement")
        
        # Active developers trend
        active_devs = project_data[project_data['Metric'] == 'GITHUB_active_developers_monthly']
        if not active_devs.empty:
            # Calculate trend
            trend = active_devs['Value'].pct_change().mean() * 100
            
            # Set alert threshold
            alert_threshold = -10  # 10% decline triggers alert
            
            # Create trend indicator
            if trend < alert_threshold:
                st.error(f"⚠️ Warning: Active developers declining by {abs(trend):.1f}% per month")
            else:
                st.success(f"✓ Active developers trend: {trend:.1f}% per month")
            
            # Plot trend
            fig = px.bar(
                active_devs,
                x='Date',
                y='Value',
                title='Active Developers Trend'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # New contributor acquisition
        new_contributors = project_data[project_data['Metric'] == 'GITHUB_new_contributors_monthly']
        if not new_contributors.empty:
            # Calculate trend
            trend = new_contributors['Value'].pct_change().mean() * 100
            
            # Set alert threshold
            alert_threshold = -20  # 20% decline triggers alert
            
            # Create trend indicator
            if trend < alert_threshold:
                st.error(f"⚠️ Warning: New contributor acquisition declining by {abs(trend):.1f}% per month")
            else:
                st.success(f"✓ New contributor trend: {trend:.1f}% per month")
            
            # Plot trend
            fig = px.bar(
                new_contributors,
                x='Date',
                y='Value',
                title='New Contributors Trend'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Development Efficiency")
        
        # PR merge time
        pr_merge_time = project_data[project_data['Metric'] == 'GITHUB_avg_prs_time_to_merge_quarterly']
        if not pr_merge_time.empty:
            # Calculate trend
            trend = pr_merge_time['Value'].pct_change().mean() * 100
            
            # Set alert threshold
            alert_threshold = 20  # 20% increase triggers alert
            
            # Create trend indicator
            if trend > alert_threshold:
                st.error(f"⚠️ Warning: PR merge time increasing by {trend:.1f}% per quarter")
            else:
                st.success(f"✓ PR merge time trend: {trend:.1f}% per quarter")
            
            # Plot trend
            fig = px.line(
                pr_merge_time,
                x='Date',
                y='Value',
                title='PR Merge Time Trend'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Issue backlog
        opened_issues = project_data[project_data['Metric'] == 'GITHUB_opened_issues_monthly']
        closed_issues = project_data[project_data['Metric'] == 'GITHUB_closed_issues_monthly']
        
        if not opened_issues.empty and not closed_issues.empty:
            # Calculate backlog ratio
            backlog_ratio = opened_issues['Value'].sum() / closed_issues['Value'].sum()
            
            # Set alert threshold
            alert_threshold = 1.5  # 1.5x more opened than closed triggers alert
            
            # Create trend indicator
            if backlog_ratio > alert_threshold:
                st.error(f"⚠️ Warning: High issue backlog (ratio: {backlog_ratio:.1f})")
            else:
                st.success(f"✓ Issue backlog ratio: {backlog_ratio:.1f}")
            
            # Plot comparison
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=opened_issues['Date'],
                y=opened_issues['Value'],
                name='Opened Issues'
            ))
            fig.add_trace(go.Bar(
                x=closed_issues['Date'],
                y=closed_issues['Value'],
                name='Closed Issues'
            ))
            fig.update_layout(
                title='Opened vs Closed Issues',
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Summary section
    st.subheader("Risk Summary")
    
    # Calculate overall risk score
    risk_factors = []
    
    if 'active_devs' in locals() and not active_devs.empty:
        if trend < alert_threshold:
            risk_factors.append("Declining contributor engagement")
    
    if 'new_contributors' in locals() and not new_contributors.empty:
        if trend < alert_threshold:
            risk_factors.append("Declining new contributor acquisition")
    
    if 'pr_merge_time' in locals() and not pr_merge_time.empty:
        if trend > alert_threshold:
            risk_factors.append("Increasing PR merge times")
    
    if 'backlog_ratio' in locals():
        if backlog_ratio > alert_threshold:
            risk_factors.append("High issue backlog")
    
    if risk_factors:
        st.error("🚨 High Risk: " + ", ".join(risk_factors))
    else:
        st.success("✅ Project health indicators are within normal ranges")

# Tab 5: Network Analysis
with tab5:
    st.header("Dependency Network Analysis")
    st.markdown("""
    ### Stylus SDK Dependency Flow
    This visualization shows how dependencies flow from package sources through package owners to dependent repositories.
    """)

    dependency_df = pd.read_csv('stylus-sdk-rs-dependencies.csv')
    
    # Add filter for number of top package owners
    top_n = st.slider(
        "Number of Top Package Owners to Show",
        min_value=10,
        max_value=200,
        value=100,
        step=10,
        help="Show the top N package owners based on number of downstream dependencies"
    )
    
    # Prepare data for Sankey diagram
    # First, count dependencies for each package owner
    package_owner_counts = dependency_df.groupby('package_repo_owner').size().reset_index(name='count')
    top_package_owners = package_owner_counts.nlargest(top_n, 'count')['package_repo_owner'].tolist()
    
    # Filter data to include only top package owners
    filtered_df = dependency_df[dependency_df['package_repo_owner'].isin(top_package_owners)]
    
    # Create source-target-value pairs for Sankey diagram
    # Level 1: package_source -> package_repo_owner
    source_target_1 = filtered_df.groupby(['package_source', 'package_repo_owner']).size().reset_index(name='value')
    source_target_1.columns = ['source', 'target', 'value']
    
    # Level 2: package_repo_owner -> seed_repo_owner
    source_target_2 = filtered_df.groupby(['package_repo_owner', 'seed_repo_owner']).size().reset_index(name='value')
    source_target_2.columns = ['source', 'target', 'value']
    
    # Combine the flows
    sankey_data = pd.concat([source_target_1, source_target_2])
    
    # Create unique list of all nodes
    all_nodes = list(set(sankey_data['source'].unique()) | set(sankey_data['target'].unique()))
    
    # Create node indices
    node_indices = {node: idx for idx, node in enumerate(all_nodes)}
    
    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=all_nodes,
            color=[
                'red' if node in filtered_df['package_source'].unique() else
                'blue' if node in filtered_df['package_repo_owner'].unique() else
                'green'
                for node in all_nodes
            ]
        ),
        link=dict(
            source=[node_indices[source] for source in sankey_data['source']],
            target=[node_indices[target] for target in sankey_data['target']],
            value=sankey_data['value'],
            color='rgba(128, 128, 128, 0.2)'
        )
    )])
    
    # Update layout
    fig.update_layout(
        title_text="Dependency Flow: Source → Package Owner → Dependent Repository",
        font_size=10,
        height=800
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show summary statistics
    st.markdown("### Flow Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Package Sources", len(filtered_df['package_source'].unique()))
    with col2:
        st.metric("Top Package Owners", len(top_package_owners))
    with col3:
        st.metric("Dependent Repositories", len(filtered_df['seed_repo_owner'].unique()))

    
