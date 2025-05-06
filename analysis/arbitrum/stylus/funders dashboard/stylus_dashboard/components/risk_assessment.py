import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
from ..config import DATA_PATHS, RISK_THRESHOLDS
from ..utils.data_processing import load_data

def render_risk_assessment():
    """Render the risk assessment tab content."""
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
                value=RISK_THRESHOLDS["active_devs_threshold"],
                step=0.5,
                help="Alert when active developers decline by more than this percentage per month"
            )
            new_contributors_threshold = st.number_input(
                "New Contributors Decline Threshold (%)",
                min_value=0.0,
                max_value=100.0,
                value=RISK_THRESHOLDS["new_contributors_threshold"],
                step=0.5,
                help="Alert when new contributor acquisition declines by more than this percentage per month"
            )
        with col2:
            pr_merge_time_threshold = st.number_input(
                "PR Merge Time Increase Threshold (%)",
                min_value=0.0,
                max_value=100.0,
                value=RISK_THRESHOLDS["pr_merge_time_threshold"],
                step=0.5,
                help="Alert when PR merge time increases by more than this percentage per quarter"
            )
            issue_backlog_threshold = st.number_input(
                "Issue Backlog Ratio Threshold",
                min_value=0.0,
                max_value=10.0,
                value=RISK_THRESHOLDS["issue_backlog_threshold"],
                step=0.1,
                help="Alert when ratio of opened to closed issues exceeds this value"
            )
    
    # Load data
    df = load_data(DATA_PATHS["stylus_metrics"])
    
    # Calculate date 120 days ago for trend analysis
    latest_date = df['sample_date'].max()
    days_ago = latest_date - timedelta(days=120)
    
    # Project selection
    all_projects = df['display_name'].unique()
    selected_project = st.selectbox(
        "Select Project for Risk Assessment",
        all_projects
    )
    
    # Filter data for selected project and last 90 days
    project_data = df[
        (df['display_name'] == selected_project) &
        (df['sample_date'] >= days_ago)
    ]
    
    # Create columns for metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Contributor Engagement")
        
        # Active developers trend
        active_devs = project_data[project_data['metric_name'] == 'GITHUB_active_developers_monthly']
        if not active_devs.empty:
            # Calculate trend
            trend = active_devs['amount'].pct_change().mean() * 100
            
            # Create trend indicator
            if trend < -active_devs_threshold:
                st.error(f"⚠️ Warning: Active developers declining by {abs(trend):.1f}% per month")
            else:
                st.success(f"✓ Active developers trend: {trend:.1f}% per month")
            
            # Plot trend
            fig = px.bar(
                active_devs,
                x='sample_date',
                y='amount',
                title='Active Developers Trend'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # New contributor acquisition
        new_contributors = project_data[project_data['metric_name'] == 'GITHUB_new_contributors_monthly']
        if not new_contributors.empty:
            # Calculate trend
            trend = new_contributors['amount'].pct_change().mean() * 100
            
            # Create trend indicator
            if trend < -new_contributors_threshold:
                st.error(f"⚠️ Warning: New contributor acquisition declining by {abs(trend):.1f}% per month")
            else:
                st.success(f"✓ New contributor trend: {trend:.1f}% per month")
            
            # Plot trend
            fig = px.bar(
                new_contributors,
                x='sample_date',
                y='amount',
                title='New Contributors Trend'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Development Efficiency")
        
        # PR merge time
        pr_merge_time = project_data[project_data['metric_name'] == 'GITHUB_avg_prs_time_to_merge_quarterly']
        if not pr_merge_time.empty:
            # Calculate trend
            trend = pr_merge_time['amount'].pct_change().mean() * 100
            
            # Create trend indicator
            if trend > pr_merge_time_threshold:
                st.error(f"⚠️ Warning: PR merge time increasing by {trend:.1f}% per quarter")
            else:
                st.success(f"✓ PR merge time trend: {trend:.1f}% per quarter")
            
            # Plot trend
            fig = px.line(
                pr_merge_time,
                x='sample_date',
                y='amount',
                title='PR Merge Time Trend'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Issue backlog
        opened_issues = project_data[project_data['metric_name'] == 'GITHUB_opened_issues_monthly']
        closed_issues = project_data[project_data['metric_name'] == 'GITHUB_closed_issues_monthly']
        
        if not opened_issues.empty and not closed_issues.empty:
            # Calculate backlog ratio
            backlog_ratio = opened_issues['amount'].sum() / closed_issues['amount'].sum()
            
            # Create trend indicator
            if backlog_ratio > issue_backlog_threshold:
                st.error(f"⚠️ Warning: High issue backlog (ratio: {backlog_ratio:.1f})")
            else:
                st.success(f"✓ Issue backlog ratio: {backlog_ratio:.1f}")
            
            # Plot comparison
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=opened_issues['sample_date'],
                y=opened_issues['amount'],
                name='Opened Issues'
            ))
            fig.add_trace(go.Bar(
                x=closed_issues['sample_date'],
                y=closed_issues['amount'],
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