import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import plotly.express as px
import networkx as nx
from PIL import Image

# Set page configuration
st.set_page_config(
    page_title="Stylus Sprint Ecosystem Dashboard",
    page_icon="📊",
    layout="wide"
)

# Display banner image
# banner_image = Image.open('./images/banner.jpg')
#col1, col2, col3 = st.columns([1, 2, 1])
#with col2:
#    st.image(banner_image)

# Main title
st.title("📊 Stylus Sprint Ecosystem Dashboard")
st.caption("Powered by [Open Source Observer](https://opensource.observer)")

st.info("""
🚧 **Under Review**  
The data and visualizations presented here are currently undergoing an audit for completeness and accuracy. Some metrics or project listings may be updated as part of this review.  
We welcome feedback and appreciate your patience as we refine the insights.
""")


# Create tabs
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",
    "Developer Ecosystem Health",
    "Stylus Sprint Activity Analysis",
    "Project Deep Dive",
    "Risk Assessment",
    "Network Analysis"
])

# Tab 0: Projects in Scope
with tab0:
    st.header("Overview")
    st.markdown("""
    Welcome to the **Stylus Sprint Ecosystem Dashboard**, a data-driven exploration of developer activity, project engagement, and network effects from the [Arbitrum Stylus Sprint](https://blog.arbitrum.io/stylus-sprint/) grant program.

    Launched by the Arbitrum DAO, Stylus Sprint is a 5 million ARB initiative supporting projects building with Stylus — a new WASM-based virtual machine that lets developers write smart contracts in Rust, C, C++, and other WebAssembly-compatible languages.

    This dashboard helps you:
    - 📋 **Overview**: Explore who's building what in the Stylus Sprint and where to dig deeper.
    - 👩‍💻 **Developer Ecosystem Health**: Uncover how developer activity is shaping the future of Stylus and Arbitrum.
    - 📈 **Stylus Sprint Activity Analysis**: Dive into engagement trends and surface signals of momentum across projects.
    - 🔍 **Project Deep Dive**: Zoom in on any project to decode its development velocity and community dynamics.
    - ⚠️ **Risk Assessment**: Spot early warning signs in project health.
    - 🕸️ **Network Analysis**: Trace the growing influence of Stylus through a web of SDK dependencies.

    Use the tabs above to explore different dimensions of the ecosystem and uncover insights into the health and momentum of Stylus-powered innovation.
    """)

    st.markdown("""
    This section lists all projects that are part of the Stylus Sprint program analysis.
    """)
    st.caption("To update your project's GitHub repositories, package links (e.g., NPM, Crates), or contract deployments in the OSS Directory, please follow the instructions outlined in [this](https://docs.google.com/document/d/1bOjjHiaY-8bx5d_Bwce4ePDYq3H7W8r_3Wq0dJCyLoA/edit?tab=t.0) document.")
    
    # Read the data files
    project_orgs = pd.read_csv('./data/project_orgs.csv')
    project_applications = pd.read_csv('./data/project_applications.csv')
    
    # Merge the dataframes
    projects_df = pd.merge(
        project_applications,
        project_orgs,
        on='project_name',
        how='left'
    )
    
    # Select and rename columns
    projects_df = projects_df[['questbook_title', 'org', 'questbook_link', 'ossd_link']]
    

    # Add GitHub URL prefix to org
    projects_df['org'] = 'https://github.com/' + projects_df['org']

    # Sort by project title
    projects_df = projects_df.sort_values('questbook_title', key=lambda x: x.str.lower())
    
    # Display the table
    st.dataframe(
        projects_df,
        column_config={
            "questbook_title": "Project Title",
            "questbook_link": st.column_config.LinkColumn("Questbook Link", display_text="Open Questbook Application"),
            "org": st.column_config.LinkColumn("GitHub Organization"),
            "ossd_link": st.column_config.LinkColumn("OSS Directory Link", display_text="Open Project YAML File")
        },
        hide_index=True,
        use_container_width=False,
        width=2000,
        height=900

    )

# Tab 1: Ecosystem Development Activity
with tab1:
    st.header("Developer Ecosystem Health")
    st.markdown("""
    This dashboard tracks active developer engagement across three key segments of the Arbitrum ecosystem:

    1. **Arbitrum Ecosystem**: Total active developers across Arbitrum projects (see note below), representing the overall health and growth of the ecosystem.
    
    2. **Stylus Grantees**: Developers actively contributing to projects in the [Arbitrum Stylus Sprint](https://arbitrum.questbook.app/dashboard/?grantId=671a105a2047c84bb8a73770&chainId=10).
    
    3. **Stylus SDK Users**: Developers building on the Stylus SDK, including both grant recipients and independent projects, showing the broader adoption of the technology.
    """)
    st.caption("Note: The Arbitrum Ecosystem data is sourced from OSS-Directory, a curated directory of open source projects on OSO. To add new projects to the directory, follow the instructions [here](https://docs.opensource.observer/docs/projects/).")
    
    # Add time window selector
    time_window = st.radio(
        "Select Time Window",
        options=["Last 3 Months", "Last 6 Months", "Last 9 Months", "Last 12 Months"],
        horizontal=True,
        index=1  # Default to 6 months
    )
    
    # Map time window to days
    time_window_days = {
        "Last 3 Months": 90,
        "Last 6 Months": 180,
        "Last 9 Months": 270,
        "Last 12 Months": 365
    }
    
    # Read and process data from all three sources
    arb_df = pd.read_csv('./data/arb_projects_active_dev_monthly.csv')
    stylus_df = pd.read_csv('./data/stylus_github_metrics.csv')
    deps_df = pd.read_csv('./data/stylus_dependencies_active_dev_monthly.csv')
    
    # Convert date columns to datetime
    for df in [arb_df, stylus_df, deps_df]:
        df['Date'] = pd.to_datetime(df['Date'])
    
    # Calculate date based on selected time window
    latest_date = max(arb_df['Date'].max(), stylus_df['Date'].max(), deps_df['Date'].max())
    # Set latest_date to end of previous month to exclude current month
    latest_date = latest_date.replace(day=1) - timedelta(days=1)
    time_ago = latest_date - timedelta(days=time_window_days[time_window])
    
    # Filter for active developers metric and selected time window
    arb_df = arb_df[
        (arb_df['Metric'] == 'GITHUB_active_developers_monthly') &
        (arb_df['Date'] >= time_ago)
    ]
    stylus_df = stylus_df[
        (stylus_df['Metric'] == 'GITHUB_active_developers_monthly') &
        (stylus_df['Date'] >= time_ago)
    ]
    deps_df = deps_df[
        (deps_df['Metric'] == 'GITHUB_active_developers_monthly') &
        (deps_df['Date'] >= time_ago)
    ]
    
    # Aggregate data by date for each context
    arb_agg = arb_df.groupby('Date')['Value'].sum().reset_index()
    stylus_agg = stylus_df.groupby('Date')['Value'].sum().reset_index()
    deps_agg = deps_df.groupby('Date')['Value'].sum().reset_index()
    
    # Calculate percentage changes for each dataset
    def calculate_pct_change(df):
        df = df.sort_values('Date')
        df['pct_change'] = df['Value'].pct_change() * 100
        return df
    
    arb_agg = calculate_pct_change(arb_agg)
    stylus_agg = calculate_pct_change(stylus_agg)
    deps_agg = calculate_pct_change(deps_agg)

    # Add summary statistics
    st.subheader(f"Average Monthly Active Developers ({time_window})")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not arb_agg.empty:
            st.metric(
                "Arbitrum Ecosystem",
                f"{arb_agg['Value'].mean():.0f}",
                f"{arb_agg['pct_change'].mean():.1f}%"
            )
        else:
            st.metric("Arbitrum Ecosystem", "No data available")
    
    with col2:
        if not stylus_agg.empty:
            st.metric(
                "Stylus Grantees",
                f"{stylus_agg['Value'].mean():.0f}",
                f"{stylus_agg['pct_change'].mean():.1f}%"
            )
        else:
            st.metric("Stylus Grantees", "No data available")
    
    with col3:
        if not deps_agg.empty:
            st.metric(
                "Stylus SDK Dependents",
                f"{deps_agg['Value'].mean():.0f}",
                f"{deps_agg['pct_change'].mean():.1f}%"
            )
        else:
            st.metric("Stylus SDK Dependents", "No data available")
    
    st.subheader(f"Monthly Active Developers Trend ({time_window})")

    # Create the figure
    fig = go.Figure()
    
    # Add traces for each context with hover text showing percentage change
    fig.add_trace(go.Scatter(
        x=arb_agg['Date'],
        y=arb_agg['Value'],
        name='Arbitrum Ecosystem',
        line=dict(color='blue', width=2),
        hovertemplate='Date: %{x}<br>Developers: %{y}<br>MoM Change: %{customdata:.1f}%<extra></extra>',
        customdata=arb_agg['pct_change']
    ))
    
    fig.add_trace(go.Scatter(
        x=stylus_agg['Date'],
        y=stylus_agg['Value'],
        name='Stylus Grantees',
        line=dict(color='green', width=2),
        hovertemplate='Date: %{x}<br>Developers: %{y}<br>MoM Change: %{customdata:.1f}%<extra></extra>',
        customdata=stylus_agg['pct_change']
    ))
    
    fig.add_trace(go.Scatter(
        x=deps_agg['Date'],
        y=deps_agg['Value'],
        name='Stylus SDK Dependents',
        line=dict(color='orange', width=2),
        hovertemplate='Date: %{x}<br>Developers: %{y}<br>MoM Change: %{customdata:.1f}%<extra></extra>',
        customdata=deps_agg['pct_change']
    ))
    
    # Add annotations for MoM changes for each data point
    def add_mom_annotations(fig, df, color, y_offset=0):
        for _, row in df.iterrows():
            if not pd.isna(row['pct_change']):
                pct_text = f"{row['pct_change']:+.1f}%"
                pct_color = 'green' if row['pct_change'] > 0 else 'red' if row['pct_change'] < 0 else 'gray'
                
                fig.add_annotation(
                    x=row['Date'],
                    y=row['Value'] + y_offset,
                    text=pct_text,
                    showarrow=False,
                    font=dict(
                        color=pct_color,
                        size=10
                    ),
                    yshift=10
                )
    
    # Add MoM annotations for each dataset with slight vertical offset to prevent overlap
    add_mom_annotations(fig, arb_agg, 'blue', 0)
    add_mom_annotations(fig, stylus_agg, 'green', 5)
    add_mom_annotations(fig, deps_agg, 'orange', -5)
    
    # Update layout
    fig.update_layout(
        #title=f'Monthly Active Developers Trend Comparison ({time_window}: {time_ago.strftime("%Y-%m-%d")} to {latest_date.strftime("%Y-%m-%d")})',
        xaxis_title='Date',
        yaxis_title='Number of Active Developers',
        height=600,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=100)  # Add more top margin to accommodate annotations
    )
    
    # Add annotations for latest values and percentage changes
    for df, name, color in [(arb_agg, 'Arbitrum Ecosystem', 'blue'),
                           (stylus_agg, 'Stylus Grantees', 'green'),
                           (deps_agg, 'Stylus SDK Dependents', 'orange')]:
        # Get the latest available date for this dataset
        dataset_latest_date = df['Date'].max()
        if not df[df['Date'] == dataset_latest_date].empty:
            latest_value = df[df['Date'] == dataset_latest_date]['Value'].iloc[0]
            latest_pct_change = df[df['Date'] == dataset_latest_date]['pct_change'].iloc[0]
            
            # Format the percentage change with appropriate color
            pct_text = f"{latest_pct_change:+.1f}%" if not pd.isna(latest_pct_change) else "N/A"
            pct_color = 'green' if latest_pct_change > 0 else 'red' if latest_pct_change < 0 else 'gray'
            
            fig.add_annotation(
                x=dataset_latest_date,
                y=latest_value,
                text=f"{name}: {latest_value}<br><span style='color:{pct_color}'>{pct_text}</span>",
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=-40,
                font=dict(color=color),
                align='left'
            )
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True)
    


    # Add top projects tables
    st.subheader(f"Top Projects by Active Developers ({time_window})")
    st.caption("Click on the column headers to sort the projects by that metric.")

    

    
    
    def calculate_project_metrics(df):
        if df.empty:
            return None
        
        # Group by project and calculate metrics
        project_metrics = df.groupby('Name').agg({
            'Value': ['mean', 'first', 'last']
        }).reset_index()
        
        # Calculate percentage change
        project_metrics['pct_change'] = ((project_metrics[('Value', 'last')] - project_metrics[('Value', 'first')]) / 
                                       project_metrics[('Value', 'first')] * 100)
        
        # Clean up columns
        project_metrics.columns = ['Project', 'Avg Devs/Month', 'First Month', 'Last Month', 'Monthly Growth %']
        project_metrics = project_metrics[['Project', 'Avg Devs/Month', 'Monthly Growth %']]
        
        # Sort and format
        project_metrics = project_metrics.sort_values('Avg Devs/Month', ascending=False).head(30)
        project_metrics['Avg Devs/Month'] = project_metrics['Avg Devs/Month'].map('{:.1f}'.format)
        
        return project_metrics
    
    def get_top_growth_projects(df, n=3, exclude_projects=None):
        if df is None or df.empty:
            return []
        # No need to convert strings to numbers since we're keeping them as numeric
        df = df.copy()
        # Exclude projects if specified
        if exclude_projects is not None:
            df = df[~df['Project'].isin(exclude_projects)]
        return df.nlargest(n, 'Monthly Growth %')[['Project', 'Monthly Growth %']].values.tolist()
    
    def style_growth(val):
        # Handle both numeric and string values
        if isinstance(val, str):
            # Extract numeric value from string (remove % and convert to float)
            try:
                num_val = float(val.rstrip('%'))
                color = 'red' if num_val < 0 else 'green'
                return f'color: {color}'
            except:
                return ''
        elif isinstance(val, (int, float)):
            color = 'red' if val < 0 else 'green'
            return f'color: {color}'
        return ''
    
    arb_projects = calculate_project_metrics(arb_df)
    stylus_projects = calculate_project_metrics(stylus_df)
    deps_projects = calculate_project_metrics(deps_df)


    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Arbitrum Ecosystem**")
        
        if arb_projects is not None:
            # Format the growth column for display
            display_df = arb_projects.copy()
            display_df['Monthly Growth %'] = display_df['Monthly Growth %'].map('{:.1f}%'.format)
            styled_df = display_df.style.applymap(style_growth, subset=['Monthly Growth %'])
            st.dataframe(styled_df, hide_index=True)
        else:
            st.write("No data available")
    
    with col2:
        st.markdown("**Stylus Grantees**")
        
        if stylus_projects is not None:
            display_df = stylus_projects.copy()
            display_df['Monthly Growth %'] = display_df['Monthly Growth %'].map('{:.1f}%'.format)
            styled_df = display_df.style.applymap(style_growth, subset=['Monthly Growth %'])
            st.dataframe(styled_df, hide_index=True)
        else:
            st.write("No data available")
    
    with col3:
        st.markdown("**Stylus SDK Dependents**")
        
        if deps_projects is not None:
            display_df = deps_projects.copy()
            display_df['Monthly Growth %'] = display_df['Monthly Growth %'].map('{:.1f}%'.format)
            styled_df = display_df.style.applymap(style_growth, subset=['Monthly Growth %'])
            st.dataframe(styled_df, hide_index=True)
        else:
            st.write("No data available")

   

# Tab 2: Overview
with tab2:
    st.header("Stylus Sprint Activity Analysis")

    st.markdown("""
    This section provides a comprehensive analysis of developer engagement and project activity within the Stylus Sprint program. 
    You'll find:
    
    - **Developer Activity Trends**: Track the evolution of active developers over time
    - **Project Activity Heatmap**: Compare key metrics (commits, issues, PRs, etc.) across all projects
    - **Time-based Analysis**: Select different time windows to analyze patterns and growth
    """)

    
    # Add time window selector
    time_window = st.radio(
        "Select a time window to analyze developer activity trends and project metrics:",
        options=["Last 3 Months", "Last 6 Months", "Last 9 Months", "Last 12 Months"],
        horizontal=True,
        index=1,  # Default to 6 months
        key="overview_time_window"  # Add unique key
    )

    st.markdown(f"### Monthly Active Developers Trend ({time_window})")

    # Map time window to days
    time_window_days = {
        "Last 3 Months": 90,
        "Last 6 Months": 180,
        "Last 9 Months": 270,
        "Last 12 Months": 365
    }

    # Read file
    df = pd.read_csv('./data/stylus_github_metrics.csv')
    
    # Convert date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Get the latest date in the dataset
    latest_date = df['Date'].max()
    
    # Calculate date based on selected time window
    time_ago = latest_date - timedelta(days=time_window_days[time_window])
    
    # Filter data for the selected time window and active developers metric
    active_devs_df = df[
        (df['Date'] >= time_ago) &
        (df['Metric'] == 'GITHUB_active_developers_monthly')
    ]
    
    # Aggregate data across all projects
    aggregated_df = active_devs_df.groupby('Date')['Value'].sum().reset_index()
    
    # Calculate percentage changes
    aggregated_df['pct_change'] = aggregated_df['Value'].pct_change() * 100
    
    # Create the figure
    fig = go.Figure()
    
    # Add trace for active developers
    fig.add_trace(go.Scatter(
        x=aggregated_df['Date'],
        y=aggregated_df['Value'],
        name='Active Developers',
        line=dict(color='blue', width=2),
        hovertemplate='Date: %{x}<br>Developers: %{y}<br>MoM Change: %{customdata:.1f}%<extra></extra>',
        customdata=aggregated_df['pct_change']
    ))
    
    # Add annotations for MoM changes
    for _, row in aggregated_df.iterrows():
        if not pd.isna(row['pct_change']):
            pct_text = f"{row['pct_change']:+.1f}%"
            pct_color = 'green' if row['pct_change'] > 0 else 'red' if row['pct_change'] < 0 else 'gray'
            
            fig.add_annotation(
                x=row['Date'],
                y=row['Value'],
                text=pct_text,
                showarrow=False,
                font=dict(
                    color=pct_color,
                    size=10
                ),
                yshift=10
            )
    
    # Update layout
    fig.update_layout(
        #title=f"Monthly Active Developers Trend ({time_window}: {time_ago.strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d')})",
        xaxis_title="Date",
        yaxis_title="Number of Active Developers",
        height=600,
        showlegend=True,
        margin=dict(t=100)  # Add more top margin to accommodate annotations
    )
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True)
    st.header(f"Project Activity Analysis ({time_window})")

    st.warning("""
    **Note:** Development metrics like commits, issues closed, and PRs merged can vary widely based on a project's workflow, team size, or codebase structure. These numbers aren’t meant for head-to-head comparisons, but rather to track changes within the same project over time. Use them as directional signals to guide deeper, qualitative evaluation.
    """)
    
    # Metric selection with radio buttons
    available_metrics = {
        'GITHUB_active_developers_monthly': 'Active Developers',
        'GITHUB_commits_monthly': 'Commits',
        'GITHUB_closed_issues_monthly': 'Closed Issues',
        'GITHUB_merged_pull_requests_monthly': 'Merged PRs',        
        'GITHUB_stars_monthly': 'Stars',
        'GITHUB_forks_monthly': 'Forks'
    }
    
    selected_metric = st.radio(
        "Select Metric for Heatmap",
        options=list(available_metrics.keys()),
        format_func=lambda x: available_metrics[x],
        horizontal=True
    )
    
    # Filter data for selected metric and time window
    heatmap_data = df[
        (df['Metric'] == selected_metric) &
        (df['Date'] >= time_ago)
    ]
    
    # Aggregate data to handle duplicates
    heatmap_data = heatmap_data.groupby(['Name', 'Date'])['Value'].sum().reset_index()
    
    # Calculate total for each project and sort
    project_totals = heatmap_data.groupby('Name')['Value'].sum().sort_values(ascending=False)
    sorted_projects = project_totals.index.tolist()
    
    # Pivot data for heatmap
    heatmap_pivot = heatmap_data.pivot(
        index='Name',
        columns='Date',
        values='Value'
    )
    
    # Reorder rows based on total values
    heatmap_pivot = heatmap_pivot.reindex(sorted_projects)
    
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
        title=f"Project Activity Heatmap - {available_metrics[selected_metric]} ({time_window})",
        height=600,
        xaxis_title="Date",
        yaxis_title="Project"
    )
    
    # Display the heatmap
    st.plotly_chart(fig, use_container_width=True)


# Tab 4: Project Deep Dive
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
    

# Tab 5: Risk Assessment
with tab4:
    st.header("Risk Assessment & Early Warning System")
    st.markdown("""
    ### Project Health Indicators
    This dashboard tracks key metrics that serve as early warning indicators for project health.
    Alerts are triggered when metrics show concerning trends over the last 3 months.
    """)

    st.warning("""
    ⚠️ This early warning system is an evolving tool designed to help identify projects that may need support. The intent is not to label risks prematurely, but to determine meaningful, configurable triggers over time — enabling the grants team to step in with timely guidance and assistance when it matters most.
    """)
    
    # Add configuration panel
    with st.expander("⚙️ Configure Alert Thresholds", expanded=False):
        st.markdown("""
        Adjust the thresholds for various risk indicators. These values determine when alerts are triggered:
        
        - **Active Developers**: Alert when monthly decline exceeds this percentage
        - **New Contributors**: Alert when monthly decline exceeds this percentage
        - **PR Merge Time**: Alert when quarterly increase exceeds this percentage
        - **Issue Backlog**: Alert when ratio of opened to closed issues exceeds this value
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            active_devs_threshold = st.number_input(
                "Active Developers Decline Threshold (%)",
                min_value=0.0,
                max_value=100.0,
                value=10.0,
                step=0.5,
                help="Alert when active developers decline by more than this percentage per month"
            )
            new_contributors_threshold = st.number_input(
                "New Contributors Decline Threshold (%)",
                min_value=0.0,
                max_value=100.0,
                value=20.0,
                step=0.5,
                help="Alert when new contributor acquisition declines by more than this percentage per month"
            )
        with col2:
            pr_merge_time_threshold = st.number_input(
                "PR Merge Time Increase Threshold (%)",
                min_value=0.0,
                max_value=100.0,
                value=20.0,
                step=0.5,
                help="Alert when PR merge time increases by more than this percentage per quarter"
            )
            issue_backlog_threshold = st.number_input(
                "Issue Backlog Ratio Threshold",
                min_value=0.0,
                max_value=10.0,
                value=1.5,
                step=0.1,
                help="Alert when ratio of opened to closed issues exceeds this value"
            )
    
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
            
            # Create trend indicator
            if trend < -active_devs_threshold:
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
            
            # Create trend indicator
            if trend < -new_contributors_threshold:
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
            
            # Create trend indicator
            if trend > pr_merge_time_threshold:
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
            
            # Create trend indicator
            if backlog_ratio > issue_backlog_threshold:
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
        if trend < -active_devs_threshold:
            risk_factors.append("Declining contributor engagement")
    
    if 'new_contributors' in locals() and not new_contributors.empty:
        if trend < -new_contributors_threshold:
            risk_factors.append("Declining new contributor acquisition")
    
    if 'pr_merge_time' in locals() and not pr_merge_time.empty:
        if trend > pr_merge_time_threshold:
            risk_factors.append("Increasing PR merge times")
    
    if 'backlog_ratio' in locals():
        if backlog_ratio > issue_backlog_threshold:
            risk_factors.append("High issue backlog")
    
    if risk_factors:
        st.error("🚨 High Risk: " + ", ".join(risk_factors))
    else:
        st.success("✅ Project health indicators are within normal ranges")

# Tab 6: Network Analysis
with tab5:
    st.header("Dependency Network Analysis")
    st.markdown("""
    ### Stylus SDK Dependency Flow
    This analysis tracks the network of dependencies for projects using the Stylus SDK for Rust. By examining package relationships and ownership patterns, we can understand how the Stylus ecosystem is growing and evolving. 
    """)

    dependency_df = pd.read_csv('./data/stylus-sdk-rs-dependencies.csv')
    
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

    
