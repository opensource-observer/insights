# Import necessary libraries
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime, timezone

# Set the Streamlit page configuration
st.set_page_config(page_title="OSO Instant Analysis", layout="wide")

# Load the dataset
code_metrics = pd.read_csv('data/code_metrics.csv')

# Convert date columns to datetime format for proper handling
code_metrics['first_commit_date'] = pd.to_datetime(code_metrics['first_commit_date'], errors='coerce')
code_metrics['last_commit_date'] = pd.to_datetime(code_metrics['last_commit_date'], errors='coerce')

# Define the desired category order for consistent presentation
desired_order = [
    'High Popularity, Actively Maintained',
    'High Popularity, Low Maintenance',
    'Niche, Actively Maintained',
    'New and Growing',
    'Moderately Maintained',
    'Mature, Low Activity',
    'Moderate Popularity, Low Activity',
    'Low Popularity, Low Activity',
    'Inactive or Abandoned',
    'Uncategorized'
]

# Function to classify projects into categories based on attributes
def classify_project(row):
    now = datetime.now(timezone.utc)
    project_age = (now - row['first_commit_date']).days if pd.notnull(row['first_commit_date']) else None
    recent_activity = (now - row['last_commit_date']).days if pd.notnull(row['last_commit_date']) else None

    if (row['star_count'] > 200 and row['fork_count'] > 100 and 
        row['developer_count'] > 10 and row['contributor_count'] > 50 and 
        row['commit_count_6_months'] > 200 and recent_activity is not None and recent_activity <= 180):
        return 'High Popularity, Actively Maintained'
    elif (row['star_count'] > 200 and row['fork_count'] > 100 and 
          4 <= row['developer_count'] <= 10 and 10 <= row['contributor_count'] <= 50 and 
          row['commit_count_6_months'] < 30 and project_age is not None and project_age > 730 and 
          recent_activity is not None and recent_activity > 180):
        return 'High Popularity, Low Maintenance'
    elif (30 <= row['star_count'] <= 200 and 10 <= row['fork_count'] <= 100 and 
          row['developer_count'] > 4 and row['contributor_count'] > 10 and 
          row['commit_count_6_months'] > 200 and recent_activity is not None and recent_activity <= 180):
        return 'Niche, Actively Maintained'
    elif (2 <= row['star_count'] <= 30 and 1 <= row['fork_count'] <= 10 and 
          1 <= row['developer_count'] <= 4 and 2 <= row['contributor_count'] <= 10 and 
          row['commit_count_6_months'] > 30 and project_age is not None and project_age <= 730 and 
          recent_activity is not None and recent_activity <= 180):
        return 'New and Growing'
    elif (row['star_count'] > 200 and row['fork_count'] > 100 and 
          row['developer_count'] < 4 and row['contributor_count'] < 10 and 
          row['commit_count_6_months'] < 30 and project_age is not None and project_age > 730 and 
          recent_activity is not None and recent_activity > 180):
        return 'Mature, Low Activity'
    elif (row['star_count'] < 2 and row['fork_count'] < 1 and 
          row['developer_count'] < 1 and row['contributor_count'] < 2 and 
          row['commit_count_6_months'] < 1 and recent_activity is not None and recent_activity > 365):
        return 'Inactive or Abandoned'
    elif (row['star_count'] < 30 and row['fork_count'] < 10 and 
          row['developer_count'] <= 4 and row['contributor_count'] <= 15 and 
          row['commit_count_6_months'] <= 12):
        return 'Low Popularity, Low Activity'
    elif (7 <= row['star_count'] <= 200 and 3 <= row['fork_count'] <= 70 and 
          2 <= row['developer_count'] <= 9 and 5 <= row['contributor_count'] <= 34 and 
          row['commit_count_6_months'] <= 23):
        return 'Moderate Popularity, Low Activity'
    elif row['commit_count_6_months'] > 50 and recent_activity is not None and recent_activity <= 180:
        return 'Moderately Maintained'
    else:
        return 'Uncategorized'

# Display the app title
st.title("Open Source Observer - Instant Analytics")

# Step 1: Select a Collection Name for analysis
selected_collection = st.selectbox(
    "Select Collection Name",
    options=[""] + sorted(code_metrics['collection_name'].unique().tolist()),  # Add an initial empty option for better UX
    format_func=lambda x: "Select a Collection" if x == "" else x
)

# Proceed only if a collection is selected
if selected_collection:
    # Filter data for the selected collection and classify projects
    filtered_code_metrics = code_metrics[code_metrics['collection_name'] == selected_collection]
    filtered_code_metrics['category'] = filtered_code_metrics.apply(classify_project, axis=1)

    # Treemap visualization to explore category distribution
    fig_treemap = px.treemap(
        filtered_code_metrics,
        path=['category', 'display_name'],
        values='developer_count',
        color='category',
        color_discrete_map={
            'High Popularity, Actively Maintained': '#87CEEB',  # Light Sky Blue
            'High Popularity, Low Maintenance': '#FFDAB9',      # Soft Peach
            'Niche, Actively Maintained': '#E6E6FA',            # Lavender
            'New and Growing': '#98FF98',                       # Mint Green
            'Moderately Maintained': '#B2DFDB',                 # Light Seafoam
            'Mature, Low Activity': '#FFF5BA',                  # Light Sand
            'Moderate Popularity, Low Activity': '#FFCCCB',     # Pale Rose
            'Low Popularity, Low Activity': '#D3D3D3',          # Light Gray
            'Inactive or Abandoned': '#F5F5DC',                 # Very Light Beige
            'Uncategorized': '#B0C4DE'                          # Light Slate Gray
        },
        title=f"Project Distribution by Category in '{selected_collection}'"
    )
    # Ensure balanced visualization dimensions
    fig_treemap.update_layout(
        width=800,
        height=800,
        margin=dict(t=40, l=0, r=0, b=0)
    )
    fig_treemap.update_traces(textfont=dict(size=18))

    # Count projects by category for bar chart visualization
    category_counts = (
        filtered_code_metrics['category']
        .value_counts()
        .reindex(desired_order, fill_value=0)
        .loc[lambda x: x > 0]  # Filter out categories with zero counts
    )

    fig_bar = px.bar(
        x=category_counts.values,
        y=category_counts.index,
        orientation='h',
        labels={'x': 'Number of Projects', 'y': 'Category'},
        color=category_counts.index,
        color_discrete_map={
            'High Popularity, Actively Maintained': '#87CEEB',
            'High Popularity, Low Maintenance': '#FFDAB9',
            'Niche, Actively Maintained': '#E6E6FA',
            'New and Growing': '#98FF98',
            'Moderately Maintained': '#B2DFDB',
            'Mature, Low Activity': '#FFF5BA',
            'Moderate Popularity, Low Activity': '#FFCCCB',
            'Low Popularity, Low Activity': '#D3D3D3',
            'Inactive or Abandoned': '#F5F5DC',
            'Uncategorized': '#B0C4DE'
        },
        title="Number of Projects by Category"
    )
    fig_bar.update_layout(showlegend=False)

    # Display insights and visualizations
    st.markdown("#### Collection Insights: Project Categories and Developer Engagement")
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.plotly_chart(fig_bar)
        st.plotly_chart(fig_treemap)

    # Allow selection of categories for deeper analysis
    st.markdown("#### Category Deep Dive")
    selected_categories = st.multiselect(
        "Select Categories for Analysis",
        options=["All"] + desired_order,
        default=["All"]
    )

    # Filter based on selected categories
    if "All" not in selected_categories:
        filtered_code_metrics = filtered_code_metrics[filtered_code_metrics['category'].isin(selected_categories)]

    # Calculate commits per active developer for scatter plot analysis
    filtered_code_metrics['commit_per_active_dev'] = (
        filtered_code_metrics['commit_count_6_months'] / 
        filtered_code_metrics['active_developer_count_6_months']
    ).fillna(0)

    # Scatter plot for deeper analysis
    fig_scatter = px.scatter(
        filtered_code_metrics,
        x='star_count',
        y='commit_per_active_dev',
        color='category',
        text='display_name',
        labels={'star_count': 'Stars (Popularity)', 'commit_per_active_dev': 'Commits per Active Developer'},
        title="Scatter Plot: Popularity vs. Developer Engagement",
        color_discrete_map={
            'High Popularity, Actively Maintained': '#87CEEB',
            'High Popularity, Low Maintenance': '#FFDAB9',
            'Niche, Actively Maintained': '#E6E6FA',
            'New and Growing': '#98FF98',
            'Moderately Maintained': '#B2DFDB',
            'Mature, Low Activity': '#FFF5BA',
            'Moderate Popularity, Low Activity': '#FFCCCB',
            'Low Popularity, Low Activity': '#D3D3D3',
            'Inactive or Abandoned': '#F5F5DC',
            'Uncategorized': '#B0C4DE'
        }
    )
    fig_scatter.update_traces(textposition='top center')
    fig_scatter.update_layout(
        width=1200,
        height=800,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    fig_scatter.update_xaxes(type="log")
    fig_scatter.update_yaxes(type="log")

    st.plotly_chart(fig_scatter)

    # Display the filtered data in a table
    st.markdown("#### Project Details")
    filtered_code_metrics = filtered_code_metrics.sort_values(by='category')
    st.dataframe(filtered_code_metrics)