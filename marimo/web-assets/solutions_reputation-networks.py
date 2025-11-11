import marimo

__generated_with = "0.17.5"
app = marimo.App(width="full")


@app.cell
def title_markdown(mo):
    mo.md(r"""
    # Who are the top developers in this ecosystem?
    """)
    return


@app.cell
def analysis_settings(mo):
    min_commits = mo.ui.slider(
        start=10,
        stop=100,
        step=10,
        value=20,
        label="Minimum Activity:"
    )
    min_repos = mo.ui.slider(
        start=1,
        stop=10,
        step=1,
        value=2,
        label="Minimum Repos:"
    )
    top_n = mo.ui.dropdown(
        options=[10, 25, 50, 100],
        value=25,
        label="Show Top N Developers:"
    )
    mo.vstack([
        mo.md("### Analysis Settings:"),
        mo.hstack([min_commits, min_repos, top_n], widths="equal", gap=2)
    ])
    return min_commits, min_repos, top_n


@app.cell
def analysis_results(df, make_treemap, min_commits, min_repos, mo, top_n):
    # Filter data based on settings
    filtered_df = df[
        (df['total_commits'] >= min_commits.value) &
        (df['repos_worked_on'] >= min_repos.value)
    ].copy()
    
    # Recalculate ranks after filtering
    filtered_df = filtered_df.sort_values('combined_score', ascending=False).reset_index(drop=True)
    filtered_df['dev_rank'] = range(1, len(filtered_df) + 1)
    
    # Get top N developers
    top_developers = filtered_df.head(top_n.value)
    
    # Calculate stats
    total_developers = len(filtered_df)
    total_trust = filtered_df['stars_received'].sum()
    total_activity = filtered_df['total_commits'].sum()
    total_repos = filtered_df['repos_worked_on'].sum()
    avg_repos_per_dev = total_repos / total_developers if total_developers > 0 else 0
    
    # Top developer info
    if len(top_developers) > 0:
        top_dev_name = top_developers.iloc[0]['developer']
        top_dev_score = top_developers.iloc[0]['combined_score']
    else:
        top_dev_name = "N/A"
        top_dev_score = 0
    
    # Generate the treemap
    _fig = make_treemap(top_developers, top_n.value)
    
    # Create stats widgets
    stat1 = mo.stat(
        label="Total Developers",
        bordered=True,
        value=f"{total_developers:,.0f}",
        caption=f"Showing top {len(top_developers)}"
    )
    stat2 = mo.stat(
        label="Trust Signals Earned",
        bordered=True,
        value=f"{total_trust:,.0f}",
        caption="By work repositories"
    )
    stat3 = mo.stat(
        label="Total Activity",
        bordered=True,
        value=f"{total_activity:,.0f}",
        caption=f"Avg: {total_activity/total_developers:,.0f} per dev"
    )
    stat4 = mo.stat(
        label="Avg Repos per Developer",
        bordered=True,
        value=f"{avg_repos_per_dev:.1f}",
        caption=f"{total_repos:,.0f} unique repos"
    )
    
    # Generate the results dashboard
    mo.vstack([
        mo.md("### Developer Network Metrics:"),
        mo.hstack([stat1, stat2, stat3, stat4], widths="equal", gap=1),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return


@app.cell
def make_treemap(px):
    def make_treemap(df, top_n):
        if len(df) == 0:
            # Return empty figure if no data
            fig = px.treemap()
            fig.update_layout(
                title="No developers match the selected criteria",
                paper_bgcolor="white",
            )
            return fig
        
        plot_df = df.copy()
        plot_df['tile_value'] = plot_df['combined_score']
        
        fig = px.treemap(
            plot_df,
            path=[px.Constant("All"), "developer"],
            values='tile_value',
            color='combined_score',
            color_continuous_scale='Greens',
            hover_data={
                "developer": True,
                "dev_rank": True,
                "combined_score": True,
                "stars_received": True,
                "total_commits": True,
                "repos_worked_on": True
            },
            title=""
        )
        
        fig.update_traces(
            pathbar=dict(visible=False),
            root_color="white",
            textfont=dict(size=12),
            marker=dict(line=dict(width=0.5, color="#222")),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Rank: %{customdata[1]}<br>"
                "Score: %{customdata[2]:,.0f}<br>"
                "Trust Signals: %{customdata[3]:,.0f}<br>"
                "Activity: %{customdata[4]:,.0f}<br>"
                "Repos: %{customdata[5]}"
                "<extra></extra>"
            )
        )
        
        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(size=12, color="#111"),
            margin=dict(t=20, l=20, r=20, b=20),
            coloraxis_showscale=False
        )
        
        return fig
    return (make_treemap,)


@app.cell
def get_data(pd):
    # Create dummy developer reputation data
    # Simulating 100 developers with varying metrics
    
    developers = []
    
    # Top tier developers (highly active, high reputation)
    top_tier_names = ['sarah-martinez', 'jchen-dev', 'alex-kumar', 'mwilliams', 'k-thompson']
    for i, name in enumerate(top_tier_names):
        developers.append({
            'developer': name,
            'stars_received': 8000 - (i * 800),
            'total_commits': 1200 - (i * 100),
            'repos_worked_on': 15 - i,
            'days_active': 365
        })
    
    # Mid tier developers (moderately active)
    mid_tier_base_names = ['fgarcia', 'grace-kim', 'henrylee', 'ipatil', 'jnguyen', 'k-anderson', 'leocodes', 
                            'mrodriguez', 'nshah', 'olivia-wang', 'patel-dev', 'qzhang', 'rachel-brown', 'ssmith', 'tlopez']
    for i, name in enumerate(mid_tier_base_names):
        developers.append({
            'developer': name,
            'stars_received': 3000 - (i * 150),
            'total_commits': 500 - (i * 20),
            'repos_worked_on': 8 - (i % 4),
            'days_active': 300 - (i * 5)
        })
    
    # Lower tier developers (less active but still contributing)
    lower_tier_prefixes = ['dev', 'code', 'eng', 'build', 'tech']
    for i in range(30):
        prefix = lower_tier_prefixes[i % len(lower_tier_prefixes)]
        developers.append({
            'developer': f'{prefix}-{(i+100):03d}',
            'stars_received': 800 - (i * 20),
            'total_commits': 200 - (i * 5),
            'repos_worked_on': 5 - (i % 3),
            'days_active': 180 - (i * 2)
        })
    
    # Newcomers (just starting out)
    newcomer_prefixes = ['js', 'py', 'go', 'rs', 'ts']
    for i in range(50):
        prefix = newcomer_prefixes[i % len(newcomer_prefixes)]
        developers.append({
            'developer': f'{prefix}-developer-{(i+200):03d}',
            'stars_received': 100 - (i * 2),
            'total_commits': 50 - i,
            'repos_worked_on': max(1, 3 - (i % 3)),
            'days_active': 60 - i
        })
    
    df = pd.DataFrame(developers)
    
    # Calculate combined score (stars weighted 2x + commits)
    df['combined_score'] = (df['stars_received'] * 2) + df['total_commits']
    
    # Sort and rank
    df = df.sort_values('combined_score', ascending=False).reset_index(drop=True)
    df['dev_rank'] = range(1, len(df) + 1)
    
    return (df,)


@app.cell
def import_libraries():
    import pandas as pd
    import plotly.express as px
    return pd, px


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return (mo,)


if __name__ == "__main__":
    app.run()

