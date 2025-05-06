import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def create_developer_trend_plot(df, title="Monthly Active Developers Trend"):
    """Create a line plot for developer trends."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['sample_date'],
        y=df['amount'],
        name='Active Developers',
        line=dict(color='blue', width=2),
        hovertemplate='Date: %{x}<br>Developers: %{y}<br>MoM Change: %{customdata:.1f}%<extra></extra>',
        customdata=df['pct_change']
    ))
    
    # Add annotations for MoM changes
    for _, row in df.iterrows():
        if not pd.isna(row['pct_change']):
            pct_text = f"{row['pct_change']:+.1f}%"
            pct_color = 'green' if row['pct_change'] > 0 else 'red' if row['pct_change'] < 0 else 'gray'
            
            fig.add_annotation(
                x=row['sample_date'],
                y=row['amount'],
                text=pct_text,
                showarrow=False,
                font=dict(color=pct_color, size=10),
                yshift=10
            )
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Number of Active Developers",
        height=600,
        showlegend=True,
        margin=dict(t=100)
    )
    
    return fig

def create_activity_heatmap(df, metric_name):
    """Create a heatmap for project activity."""
    # Pivot data for heatmap
    heatmap_pivot = df.pivot(
        index='display_name',
        columns='sample_date',
        values='amount'
    )
    
    # Create heatmap
    fig = px.imshow(
        heatmap_pivot,
        labels=dict(
            x="Date",
            y="Project",
            color=metric_name
        ),
        aspect="auto",
        color_continuous_scale="Viridis"
    )
    
    fig.update_layout(
        title=f"Project Activity Heatmap - {metric_name}",
        height=600,
        xaxis_title="Date",
        yaxis_title="Project"
    )
    
    return fig

def create_sankey_diagram(dependency_df, top_n=100):
    """Create a Sankey diagram for dependency analysis."""
    # Prepare data for Sankey diagram
    package_owner_counts = dependency_df.groupby('package_repo_owner').size().reset_index(name='count')
    top_package_owners = package_owner_counts.nlargest(top_n, 'count')['package_repo_owner'].tolist()
    
    filtered_df = dependency_df[dependency_df['package_repo_owner'].isin(top_package_owners)]
    
    # Create source-target-value pairs
    source_target_1 = filtered_df.groupby(['package_source', 'package_repo_owner']).size().reset_index(name='value')
    source_target_1.columns = ['source', 'target', 'value']
    
    source_target_2 = filtered_df.groupby(['package_repo_owner', 'seed_repo_owner']).size().reset_index(name='value')
    source_target_2.columns = ['source', 'target', 'value']
    
    sankey_data = pd.concat([source_target_1, source_target_2])
    
    # Create unique list of all nodes
    all_nodes = list(set(sankey_data['source'].unique()) | set(sankey_data['target'].unique()))
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
    
    fig.update_layout(
        title_text="Dependency Flow: Source → Package Owner → Dependent Repository",
        font_size=10,
        height=800
    )
    
    return fig 