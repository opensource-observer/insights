import marimo

__generated_with = "0.16.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# RF4 Ballot Box Analysis""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    The voting results for Optimism's Retro Funding Round 4 (RF4) were tallied in July 2024 and shared with the community.

    This is an analysis of the ballot data from different angles. First, we cover high-level trends among voters. Then, we compare voters' expressed preferences (from a pre-round survey) against their revealed preferences (from the voting data). Finally, we perform some clustering analysis on the votes and identify three distinct "blocs" of voters.

    **Round Overview:**

    - **10M OP tokens** distributed across **230 projects**
    - **108 badgeholders** voted (out of ~130 eligible)
    - **16 impact metrics** available for selection
    - Each project was pre-scored against all metrics
    - Each badgeholder voted on the metrics they believed best assessed impact on the Superchain

    The final distribution was determined by taking the median allocation across all badgeholder ballots, with a maximum cap of 500K OP per project and a minimum threshold of 1K OP.
    """
    )
    return


@app.cell
def _(DF_METRICS, METRIC_IDS_RF4, client, json, pd):
    TOTAL_FUNDING = 10_000_000
    MAX_CAP = 500_000
    MIN_CAP = 1000


    def parse_payload(json_payload):
        """
        Parse the JSON payload into a dictionary with allocations and OS multiplier.
        """
        ballot = json.loads(json_payload)
        allocations = {
            metric_id: weight
            for metric_dict in ballot['allocations']
            for metric_id, weight in metric_dict.items()
        }
        return {'allocations': allocations, 'os_multiplier': ballot['os_multiplier']}


    def score_projects(ballot):
        """
        Score projects based on the ballot's allocations and the OS multiplier.
        """
        os_multiplier = DF_METRICS['is_oss'].apply(lambda x: ballot['os_multiplier'] if x else 1)
        scores = DF_METRICS[METRIC_IDS_RF4].copy()

        for metric in METRIC_IDS_RF4:
            scores[metric] *= os_multiplier
            scores[metric] /= scores[metric].sum()
            weight = ballot['allocations'].get(metric, 0) / 100.0
            scores[metric] *= weight

        return scores.sum(axis=1)


    def allocate_funding(project_scores, funding_balance=TOTAL_FUNDING):
        """
        Allocate funding to projects based on their scores.
        """
        allocations = {}
        score_balance = project_scores.sum()

        for project_id, score in project_scores.sort_values(ascending=False).items():
            uncapped_funding_alloc = score / score_balance * funding_balance
            capped_funding_alloc = min(uncapped_funding_alloc, MAX_CAP)
            allocations[project_id] = capped_funding_alloc
            funding_balance -= capped_funding_alloc
            score_balance -= score

        return pd.Series(allocations)


    def determine_results(df_ballots, total_funding=TOTAL_FUNDING, max_cap=MAX_CAP, min_cap=MIN_CAP):
        """
        Determine the results of the Retro Funding 4 round.
        """
        # 1. score each ballot
        df_scores = df_ballots.apply(score_projects)

        # 2. allocate funding for each badgeholder
        df_results = df_scores.apply(allocate_funding, axis=1).T

        # 3. get the median funding for each project
        df_results['median'] = df_results.median(axis=1)

        # 4. allocate funding based on the median badgeholder allocation
        df_results['rf4_allocation'] = allocate_funding(df_results['median'])

        # 5. set the funding for projects below the minimum cap to 0
        df_results.loc[df_results['rf4_allocation'] < MIN_CAP, 'rf4_allocation'] = 0

        # 6. allocate the remaining funding to projects below the maximum cap
        max_cap_funding = df_results[df_results['rf4_allocation']==MAX_CAP]['rf4_allocation'].sum()
        remaining_funding = TOTAL_FUNDING - max_cap_funding
        df_remaining = df_results[df_results['rf4_allocation']<MAX_CAP]
        df_results['rf4_allocation'].update(allocate_funding(df_remaining['rf4_allocation'], remaining_funding))

        return df_results


    _df_votes = client.to_pandas("SELECT payload FROM oso__gsheets.default.rf4_ballots")
    VOTES = _df_votes['payload'].apply(parse_payload)
    allocations = [v['allocations'] for v in VOTES]
    DF_VOTES = pd.DataFrame(allocations) / 100
    METRIC_IDS = DF_VOTES.mean().sort_values(ascending=False).index
    os_multiply = [v['os_multiplier'] for v in VOTES]
    DF_VOTES['os_multiplier'] = os_multiply

    RESULTS = determine_results(
        VOTES,
        total_funding=TOTAL_FUNDING,
        max_cap=MAX_CAP,
        min_cap=MIN_CAP
    )
    return DF_VOTES, METRIC_IDS, RESULTS, VOTES, determine_results


@app.cell
def _(client, pd):
    DF_SURVEY = client.to_pandas("SELECT * FROM oso__gsheets.default.rf4_surveys")
    DF_SURVEY = DF_SURVEY.iloc[:,[1,2,3,4,5,6,8,9,10]]
    DF_SURVEY.columns = ['user_growth_or_user_quality', 'onboarding_new_users', 'retaining_users', 'engaging_trusted_users', 'maintaining_high_levels_of_daily_activity', 'attracting_loyal_power_users', 'network_activity_growth_or_quality', 'generating_blockspace_demand', 'using_open_source_and_permissive_licenses']
    GENERAL_PREFS = ['user_growth_or_user_quality', 'network_activity_growth_or_quality']
    SPECIFIC_PREFS = [c for c in DF_SURVEY.columns if c not in GENERAL_PREFS]
    DF_SURVEY = DF_SURVEY[GENERAL_PREFS + SPECIFIC_PREFS]
    DF_SURVEY.dropna(inplace=True)
    for _pref in GENERAL_PREFS:
        DF_SURVEY[_pref] = DF_SURVEY[_pref].apply(lambda x: x.split(' ')[0])
    # Convert SPECIFIC_PREFS columns to numeric
    for _pref in SPECIFIC_PREFS:
        DF_SURVEY[_pref] = pd.to_numeric(DF_SURVEY[_pref], errors='coerce')
    return DF_SURVEY, SPECIFIC_PREFS


@app.cell
def _(pd):
    # load the Impact Metrics as a global dataframe
    METRICS_CSV_PATH = "https://raw.githubusercontent.com/opensource-observer/insights/refs/heads/main/analysis/optimism/retrofunding4/data/op_rf4_impact_metrics_by_project.csv"
    DF_METRICS = pd.read_csv(METRICS_CSV_PATH, index_col=1)
    METRIC_IDS_RF4 = DF_METRICS.columns[-16:]
    return DF_METRICS, METRIC_IDS_RF4


@app.cell
def _():
    # Add metrics to groups
    METRIC_GROUPS = {
        'gas_fees': [
            'log_gas_fees',
            'gas_fees'
        ],
        'txn_counts': [
            'log_transaction_count',
            'transaction_count'
        ],
        'trusted_txn_counts': [
            'log_trusted_transaction_count', 
            'trusted_transaction_count'
        ],
        'trusted_users': [
            'trusted_daily_active_users',
            'trusted_monthly_active_users',
            'trusted_transaction_count',
            'log_trusted_transaction_count',
            'trusted_transaction_share',
            'trusted_users_onboarded',
            'openrank_trusted_users_count',
            'trusted_recurring_users'
        ],
        'logs': [
            'log_gas_fees',
            'log_transaction_count',
            'log_trusted_transaction_count'
        ],
        'network_growth': [
            'gas_fees',
            'log_gas_fees',
            'transaction_count',
            'log_transaction_count'
        ],
        'network_quality': [
            'trusted_transaction_count',
            'log_trusted_transaction_count',
            'trusted_transaction_share'
        ],
        'user_growth': [
            'daily_active_addresses',
            'monthly_active_addresses',
            'power_user_addresses',
            'recurring_addresses'
        ],
        'user_quality': [
            'trusted_daily_active_users',
            'trusted_monthly_active_users',
            'trusted_recurring_users',
            'trusted_users_onboarded',
            'openrank_trusted_users_count'
        ]
    }
    return (METRIC_GROUPS,)


@app.cell
def _():
    # Chart templates - not visible to readers
    return


@app.cell
def _(COLOR1, FONT_SIZE, METRIC_IDS, TITLE_SIZE, go, pd):
    def barchart(lst, title, top_n=100):
        series = pd.Series(lst).sort_values(ascending=False).head(top_n) / 1000
        xmax = len(series)
        med = series.median()
        top10 = series.quantile(0.9)

        _fig = go.Figure()

        # Add bar chart
        _fig.add_trace(go.Bar(
            x=list(range(len(series))),
            y=series.values,
            marker=dict(color=COLOR1, opacity=0.5),
            showlegend=False
        ))

        # Add median line
        _fig.add_hline(
            y=med, 
            line=dict(color='grey', dash='dash', width=1)
        )

        # Add top 10% line
        _fig.add_hline(
            y=top10,
            line=dict(color='grey', dash='dash', width=1)
        )

        # Update layout
        _fig.update_layout(
            title=dict(text=f'<b>{title}</b>', x=0, xanchor='left', font=dict(size=TITLE_SIZE)),
            xaxis=dict(
                title='Project Rank',
                tickmode='array',
                tickvals=list(range(0, xmax, 25)),
                ticktext=list(range(0, xmax, 25)),
                range=[0, xmax],
                tickfont=dict(size=FONT_SIZE)
            ),
            yaxis=dict(
                title='Funding (OP)',
                tickmode='array',
                tickvals=[0, 100, 200, 300, 400, 500],
                ticktext=[0, 100, 200, 300, 400, '500K'],
                range=[0, 500],
                tickfont=dict(size=FONT_SIZE)
            ),
            height=288,
            width=1440,
            font=dict(family='Arial', size=FONT_SIZE),
            paper_bgcolor='white',
            plot_bgcolor='white',
            margin=dict(l=60, r=20, t=60, b=60)
        )

        # Add annotations separately
        _fig.add_annotation(
            x=xmax,
            y=med,
            text=f'Median: {med:.0f}K OP',
            xref='x',
            yref='y',
            xanchor='right',
            yanchor='bottom',
            showarrow=False,
            font=dict(size=FONT_SIZE)
        )

        _fig.add_annotation(
            x=xmax,
            y=top10,
            text=f'Top 10%: {top10:.0f}K OP',
            xref='x',
            yref='y',
            xanchor='right',
            yanchor='bottom',
            showarrow=False,
            font=dict(size=FONT_SIZE)
        )

        return _fig

    def stripplot(dataframe, subtitle):
        vote_weights = (dataframe[METRIC_IDS].fillna(0).mean() * 100).sort_values(ascending=False)
        metric_order = vote_weights.index
        vote_counts = dataframe[metric_order].count()
        unstacked_votes = dataframe[metric_order].unstack().reset_index()
        unstacked_votes.columns = ['metric', 'voter', 'weight']

        # Drop rows with NaN weights
        unstacked_votes = unstacked_votes.dropna(subset=['weight'])

        _fig = go.Figure()

        # Add strip plot points for each metric
        for metric in metric_order:
            _metric_data = unstacked_votes[unstacked_votes['metric'] == metric]
            if len(_metric_data) > 0:
                _fig.add_trace(go.Scatter(
                    x=_metric_data['weight'],
                    y=[metric] * len(_metric_data),
                    mode='markers',
                    marker=dict(
                        size=8,
                        color=_metric_data['weight'],
                        colorscale='Reds',
                        cmin=0,
                        cmax=0.2,
                        opacity=0.5,
                        line=dict(width=0)
                    ),
                    showlegend=False,
                    hovertemplate='%{x:.1%}<extra></extra>'
                ))

        # Create y-axis labels with vote counts and weights
        _ytick_labels = []
        _ytick_annotations = []
        for i, metric in enumerate(metric_order):
            _n = vote_counts.get(metric, 0)
            _w = vote_weights.get(metric, 0)
            _label = metric.replace('_', ' ').title().replace('Log', '(Log)')
            _ytick_labels.append(_label)
            _ytick_annotations.append(f'{int(_n)} votes, {_w:.0f}% avg')

        # Update layout
        _fig.update_layout(
            title=dict(
                text=f'<b>Distribution of impact metric weights by ballot - {subtitle}</b>',
                x=0,
                xanchor='left',
                font=dict(size=TITLE_SIZE)
            ),
            xaxis=dict(
                tickmode='array',
                tickvals=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1],
                ticktext=['0%', '10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '100%'],
                range=[-0.02, 1.02],
                tickfont=dict(size=FONT_SIZE),
                showgrid=True,
                gridcolor='grey',
                gridwidth=0.5
            ),
            yaxis=dict(
                tickmode='array',
                tickvals=list(metric_order),
                ticktext=_ytick_labels,
                tickfont=dict(size=FONT_SIZE)
            ),
            height=720,
            width=1440,
            font=dict(family='Arial', size=FONT_SIZE),
            paper_bgcolor='white',
            plot_bgcolor='white',
            margin=dict(l=300, r=250, t=80, b=60)
        )

        # Add annotations for vote counts on the right side
        for i, (metric, annotation) in enumerate(zip(metric_order, _ytick_annotations)):
            _fig.add_annotation(
                x=1.06,
                y=metric,
                text=annotation,
                xref='paper',
                yref='y',
                showarrow=False,
                xanchor='left',
                font=dict(size=FONT_SIZE)
            )

        return _fig
    return barchart, stripplot


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## 1. High-Level Observations""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Let's start by examining how badgeholders approached the voting process and what patterns emerged from their ballots.""")
    return


@app.cell(hide_code=True)
def _(DF_VOTES, METRIC_IDS, mo):
    _total_votes_stat = mo.stat(
        label="Total Ballots",
        value=f"{len(DF_VOTES)}",
        bordered=True
    )

    _total_metrics_stat = mo.stat(
        label="Impact Metrics Available",
        value=f"{len(METRIC_IDS)}",
        bordered=True
    )

    _median_metrics_stat = mo.stat(
        label="Median Metrics Per Ballot",
        value=f"{DF_VOTES[METRIC_IDS].count(axis=1).median():.0f}",
        bordered=True
    )

    mo.hstack([_total_votes_stat, _total_metrics_stat, _median_metrics_stat], widths="equal")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### The average badgeholder voted on five metrics

    While a few voters included all 16 metrics, most selected between 3 to 6 metrics. Some metrics were closely related, such as `gas_fees` and `log_gas_fees`, which represented the same metric on different scales (linear vs logarithmic). Half of the metrics relied on a "trusted user model", considering different aspects of user and network activity.
    """
    )
    return


@app.cell
def _(COLOR1, DF_VOTES, FONT_SIZE, METRIC_IDS, TITLE_SIZE, go, mo):
    _counts = DF_VOTES[METRIC_IDS].count(axis=1)

    _fig = go.Figure()
    _fig.add_trace(go.Histogram(
        x=_counts,
        xbins=dict(start=-0.5, end=16.5, size=1),
        marker=dict(color=COLOR1),
        showlegend=False
    ))

    _fig.update_layout(
        title=dict(text='<b>Histogram of metrics selected per ballot</b>', x=0, xanchor='left', font=dict(size=TITLE_SIZE)),
        xaxis=dict(
            title='Number of metrics',
            tickmode='array',
            tickvals=list(range(0, 17)),
            tickfont=dict(size=FONT_SIZE)
        ),
        yaxis=dict(
            title='Number of ballots',
            tickfont=dict(size=FONT_SIZE)
        ),
        height=432,
        width=1440,
        font=dict(family='Arial', size=FONT_SIZE),
        paper_bgcolor='white',
        plot_bgcolor='white',
        margin=dict(l=60, r=20, t=60, b=60),
        bargap=0.1
    )

    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### Badgeholders felt gas fees were the most impactful metric

    The chart below ranks each metric based on its overall weighting and shows the distribution of individual votes. `gas_fees` topped the list, receiving votes from 60 badgeholders and accounting for 19% of the total allocation. The `trusted_users_onboarded` metric was the most popular individual indicator, attracting 75 votes but weighing less than `gas_fees` in the final allocation.
    """
    )
    return


@app.cell
def _(DF_VOTES, mo, stripplot):
    mo.ui.plotly(stripplot(DF_VOTES, "all votes"))
    return


@app.cell(hide_code=True)
def _(DF_VOTES, METRIC_GROUPS, mo):
    _summary_text = []
    for grouping, metric_list in METRIC_GROUPS.items():
        filt = DF_VOTES[metric_list].sum(axis=1)
        num_metrics = len(metric_list)
        _n = len(filt[filt > 0])
        m = filt.mean() * 100
        _summary_text.append(f"- **{grouping.replace('_', ' ').title()}** ({num_metrics} metrics): {_n} ballots, {m:.1f}% avg weight<br>")

    mo.md(
        r"""
        Combining related metrics reveals interesting patterns:

        """ + "\n".join(_summary_text) + """

        Most notably, `gas_fees` and `log_gas_fees` appeared in 94 out of 108 ballots and commanded 31% of the total weighting. Metrics derived from the trusted user model were included in 92 ballots, representing 44% of the weighting.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### The final distribution was a power law distribution

    Previous rounds, including Optimism's RF3 and Filecoin's RetroPGF 1, had relatively flat distributions. In RF3, the median project received 45K OP, while a top 10% project received 100K OP. In RF4, despite having a smaller overall funding pool (10M vs 30M tokens), the distribution was much steeper, with top projects doing significantly better.
    """
    )
    return


@app.cell(hide_code=True)
def _(RESULTS, mo):
    _median_alloc = mo.stat(
        label="Median Project Allocation",
        value=f"{RESULTS['rf4_allocation'].median()/1000:.0f}K OP",
        bordered=True
    )

    _top10_alloc = mo.stat(
        label="Top 10% Project Allocation",
        value=f"{RESULTS['rf4_allocation'].quantile(0.9)/1000:.0f}K OP",
        bordered=True
    )

    _ratio = mo.stat(
        label="Top 10% to Median Ratio",
        value=f"{RESULTS['rf4_allocation'].quantile(0.9)/RESULTS['rf4_allocation'].median():.0f}x",
        bordered=True
    )

    mo.hstack([_median_alloc, _top10_alloc, _ratio], widths="equal")
    return


@app.cell
def _(RESULTS, barchart, mo):
    mo.ui.plotly(barchart(RESULTS['rf4_allocation'], title='Overall RF4 distribution', top_n=230))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## 2. Expressed vs Revealed Preferences""")
    return


@app.cell(hide_code=True)
def _(DF_VOTES, mo):
    mo.md(
        f"""
    Before the voting phase, a survey was conducted to understand badgeholders' preferences. We can compare these **expressed preferences** from the survey against their **revealed preferences** from the actual voting data to see how well they align.

    The survey received **38 responses** from badgeholders, while **{len(DF_VOTES)} badgeholders** ultimately voted in the round.
    """
    )
    return


@app.cell
def _(COLOR1, DF_SURVEY, FONT_SIZE, SPECIFIC_PREFS, TITLE_SIZE, go, mo):
    _fig = go.Figure()

    for col in SPECIFIC_PREFS:
        _fig.add_trace(go.Box(
            x=DF_SURVEY[col],
            name=col.replace('_', ' ').title(),
            marker=dict(color=COLOR1),
            orientation='h',
        ))

    _fig.update_layout(
        title=dict(text='<b>Badgeholder preferences in survey data (n=38)</b>', x=0, xanchor='left', font=dict(size=TITLE_SIZE)),
        height=720,
        width=1440,
        font=dict(family='Arial', size=FONT_SIZE),
        paper_bgcolor='white',
        plot_bgcolor='white',
        margin=dict(l=300, r=20, t=60, b=60),
        showlegend=False,
        yaxis=dict(tickfont=dict(size=FONT_SIZE)),
        xaxis=dict(tickfont=dict(size=FONT_SIZE))
    )

    mo.ui.plotly(_fig)
    return


@app.cell
def _(
    COLOR1,
    DF_SURVEY,
    DF_VOTES,
    FONT_SIZE,
    METRIC_GROUPS,
    TITLE_SIZE,
    go,
    mo,
    pd,
):
    comparison = {
        'Network Growth': {
            'Survey': len(DF_SURVEY[DF_SURVEY['network_activity_growth_or_quality'] == 'Growth']) / len(DF_SURVEY),
            'Votes': DF_VOTES[METRIC_GROUPS['network_growth']].sum(axis=1).mean()
        },
        'Network Quality': {
            'Survey': len(DF_SURVEY[DF_SURVEY['network_activity_growth_or_quality'] == 'Quality']) / len(DF_SURVEY),
            'Votes': DF_VOTES[METRIC_GROUPS['network_quality']].sum(axis=1).mean()
        },
        'User Growth': {
            'Survey': len(DF_SURVEY[DF_SURVEY['user_growth_or_user_quality'] == 'Growth']) / len(DF_SURVEY),
            'Votes': DF_VOTES[METRIC_GROUPS['user_growth']].sum(axis=1).mean()
        },
        'User Quality': {
            'Survey': len(DF_SURVEY[DF_SURVEY['user_growth_or_user_quality'] == 'Quality']) / len(DF_SURVEY),
            'Votes': DF_VOTES[METRIC_GROUPS['user_quality']].sum(axis=1).mean()
        }    
    }

    _df_comparison = pd.DataFrame(comparison).T

    _fig = go.Figure()

    # Add Survey line
    _fig.add_trace(go.Scatter(
        x=_df_comparison.index,
        y=_df_comparison['Survey'],
        mode='lines+markers',
        name='Survey',
        line=dict(color=COLOR1, width=2, dash='dash'),
        marker=dict(size=8)
    ))

    # Add Votes line
    _fig.add_trace(go.Scatter(
        x=_df_comparison.index,
        y=_df_comparison['Votes'],
        mode='lines+markers',
        name='Votes',
        line=dict(color=COLOR1, width=2),
        marker=dict(size=8)
    ))

    _fig.update_layout(
        title=dict(text='<b>Comparison of survey preferences vs voting preferences</b>', x=0, xanchor='left', font=dict(size=TITLE_SIZE)),
        xaxis=dict(tickfont=dict(size=FONT_SIZE)),
        yaxis=dict(
            title='Strength of preference',
            tickmode='array',
            tickvals=[0, 0.25, 0.50],
            ticktext=['', '25%', '50%'],
            range=[0, 0.6],
            tickfont=dict(size=FONT_SIZE)
        ),
        height=432,
        width=1440,
        font=dict(family='Arial', size=FONT_SIZE),
        paper_bgcolor='white',
        plot_bgcolor='white',
        margin=dict(l=60, r=20, t=60, b=60),
        legend=dict(x=1, y=1, xanchor='right', yanchor='top')
    )

    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### User quality was rewarded over growth

    In the survey, voters preferred rewarding user quality over growth (47% vs 24%). This preference was reflected in the voting data, with user quality metrics appearing on 89 out of 108 ballots and receiving 35% of the overall allocation. User growth metrics appeared on 69 ballots, accounting for 15% of the allocation.

    ### Network growth metrics performed better than network quality metrics

    In contrast to the user metrics, voters showed a stronger preference for network growth metrics (e.g., `gas_fees` and `transaction_counts`). While survey respondents preferred quality over growth (39% vs 16%), network growth metrics appeared on 98 ballots, capturing 41% of the allocation. Network quality metrics appeared on 47 ballots, receiving just 9% of the overall allocation.

    **Possible reasons for the discrepancy:**

    1. **Non-representative survey sample**: Only 38 badgeholders completed the survey versus 108 who voted. Badgeholders caring more about social and quality metrics might have been overrepresented in the survey.

    2. **Change of mind**: Voters may have adjusted preferences after reviewing specific metrics, reading others' strategies, or seeing the actual project mix in the voting UI. There was over a month between the survey and voting phases.

    3. **Weak metrics**: Network quality metrics might have been perceived as less impactful. Metrics like gas efficiency and novel implementations did not make the final cut, suggesting a need for better quality metrics in future rounds.

    ### Consistency in specific metrics

    Voters' preferences remained consistent around specific metrics like onboarding and retaining users. Although controversial and difficult to assess, the open source multiplier was popular both before and during the round: 87% of survey respondents valued rewarding open source projects, and 80% of voters used the open source multiplier in their ballots.
    """
    )
    return


@app.cell
def _():
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## 3. Correlations and Badgeholder Blocs""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""As votes were public, we can analyze the data to identify patterns and groupings among voters. This helps us understand how different groups of badgeholders approached the voting process and what impact this had on the final distribution.""")
    return


@app.cell
def _(METRIC_GROUPS):
    corr_order = (
        METRIC_GROUPS['network_growth']
        + METRIC_GROUPS['user_growth']
        + METRIC_GROUPS['network_quality']
        + METRIC_GROUPS['user_quality']
    )
    return (corr_order,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### Some metrics had correlated performance among voters

    The correlation matrix below shows the degree to which any two metrics were positively or negatively correlated. `gas_fees`, for instance, correlated most strongly with `transaction_count` but little else. Most trusted user metrics had moderate to high correlation coefficients. The most pronounced negative correlation was between `log_trusted_transaction_count` and `daily_active_addresses`, both among the least popular metrics.
    """
    )
    return


@app.cell
def _(DF_VOTES, FONT_SIZE, TITLE_SIZE, corr_order, go, mo):
    _corr_matrix = DF_VOTES[corr_order].corr()

    # Format labels
    _labels = [col.replace('_', ' ').title().replace('Log', '(Log)') for col in _corr_matrix.columns]

    _fig = go.Figure(data=go.Heatmap(
        z=_corr_matrix.values,
        x=_labels,
        y=_labels,
        colorscale='RdBu_r',
        zmid=0,
        text=_corr_matrix.values.round(2),
        texttemplate='%{text}',
        textfont=dict(size=8),
        showscale=False,
        xgap=1,
        ygap=1
    ))

    _fig.update_layout(
        title=dict(text='<b>Correlations between impact metrics</b>', x=0, xanchor='left', font=dict(size=TITLE_SIZE)),
        height=1440,
        width=1440,
        font=dict(family='Arial', size=FONT_SIZE),
        paper_bgcolor='white',
        plot_bgcolor='white',
        margin=dict(l=250, r=20, t=80, b=250),
        xaxis=dict(
            tickangle=45,
            side='bottom',
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            tickfont=dict(size=10)
        )
    )

    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### We identified three distinct "blocs" of voters using a clustering algorithm

    A voting bloc is a group of voters strongly motivated by specific concerns, leading them to vote together. Using a k-means clustering algorithm on the ballot allocations, we identified three distinct blocs with different preferences in the voting data.
    """
    )
    return


@app.cell
def _(DF_VOTES, METRIC_IDS, pd):
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans

    votes_df = DF_VOTES[METRIC_IDS].copy().fillna(0)
    scaler = StandardScaler()
    scaled_votes = scaler.fit_transform(votes_df)

    _kmeans = KMeans(n_clusters=3, random_state=42)
    votes_df['Cluster'] = _kmeans.fit_predict(scaled_votes)

    centroids = pd.DataFrame(
        scaler.inverse_transform(_kmeans.cluster_centers_),
        columns=votes_df.columns[:-1])
    centroids['Cluster'] = centroids.index
    centroids.sort_values(by='gas_fees', inplace=True)
    centroids['Bloc'] = ['Trust Bloc', 'Balanced Bloc', 'Gas Bloc']
    blocs = centroids.set_index('Cluster')['Bloc'].to_dict()

    votes_df['Bloc'] = votes_df['Cluster'].apply(lambda x: blocs.get(x, "Balanced Bloc"))
    return (votes_df,)


@app.cell
def _(VOTES, barchart, determine_results, votes_df):
    def bloc_distribution(bloc):
        voting_bloc = votes_df[votes_df['Bloc'] == bloc].index
        bloc_results = determine_results(VOTES[voting_bloc])['rf4_allocation'].sort_values()
        return barchart(bloc_results, f"'{bloc}' distribution", top_n=230)
    return (bloc_distribution,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### The "Trust Bloc" experimented with trusted user metrics and had more diverse ballots overall

    This largest bloc, effectively a catchall for nuanced views on rewarding impact or a preference for consumer-oriented apps, gave greater allocation to user metrics over network activity. These voters generally kept allocations below 40% per metric, resulting in a more balanced weight across all 16 metrics.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo, votes_df):
    _trust_count = len(votes_df[votes_df['Bloc'] == 'Trust Bloc'])
    _trust_pct = _trust_count / len(votes_df) * 100

    _trust_stat = mo.stat(
        label="Trust Bloc Size",
        value=f"{_trust_count} voters ({_trust_pct:.0f}%)",
        bordered=True
    )

    mo.hstack([_trust_stat], widths="equal")
    return


@app.cell
def _(bloc_distribution, mo, stripplot, votes_df):
    _bloc = 'Trust Bloc'
    mo.vstack([
        mo.ui.plotly(stripplot(votes_df[votes_df['Bloc'] == _bloc], subtitle=_bloc)),
        mo.ui.plotly(bloc_distribution(_bloc))
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### The "Balanced Bloc" liked log metrics and a flatter overall distribution

    This bloc seemed to want to achieve a more balanced distribution of tokens among projects. They favored network growth indicators on a log scale, allocating over 40% to `log_gas_fees` and `log_transaction_count`. They also used address-based metrics more than trusted user metrics. The simulated token distribution for this bloc had a 6-to-1 ratio between a top 10% project and a median project, compared to 16-to-1 for the Gas Bloc (and 9-to-1 for the actual distribution).
    """
    )
    return


@app.cell(hide_code=True)
def _(mo, votes_df):
    _balanced_count = len(votes_df[votes_df['Bloc'] == 'Balanced Bloc'])
    _balanced_pct = _balanced_count / len(votes_df) * 100

    _balanced_stat = mo.stat(
        label="Balanced Bloc Size",
        value=f"{_balanced_count} voters ({_balanced_pct:.0f}%)",
        bordered=True
    )

    mo.hstack([_balanced_stat], widths="equal")
    return


@app.cell
def _(bloc_distribution, mo, stripplot, votes_df):
    _bloc = 'Balanced Bloc'
    mo.vstack([
        mo.ui.plotly(stripplot(votes_df[votes_df['Bloc'] == _bloc], subtitle=_bloc)),
        mo.ui.plotly(bloc_distribution(_bloc))
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### The "Gas Bloc" emphasized gas fees

    Gas fees, a simple impact metric, formed the basis of many ballots. All voters in this bloc allocated over 20% of their ballot to `gas_fees`, averaging 47%. Including `log_gas_fees`, the weighting rose to 54%. This bloc showed little interest in other metrics. Had everyone voted like the Gas Bloc, the results distribution would have been more exponential, with a much steeper curve favoring the top projects.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo, votes_df):
    _gas_count = len(votes_df[votes_df['Bloc'] == 'Gas Bloc'])
    _gas_pct = _gas_count / len(votes_df) * 100

    _gas_stat = mo.stat(
        label="Gas Bloc Size",
        value=f"{_gas_count} voters ({_gas_pct:.0f}%)",
        bordered=True
    )

    mo.hstack([_gas_stat], widths="equal")
    return


@app.cell
def _(bloc_distribution, mo, stripplot, votes_df):
    _bloc = 'Gas Bloc'
    mo.vstack([
        mo.ui.plotly(stripplot(votes_df[votes_df['Bloc'] == _bloc], subtitle=_bloc)),
        mo.ui.plotly(bloc_distribution(_bloc))
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Final Thoughts

    This analysis prompts some important governance questions for the Optimism community:

    - **Alignment**: How well do citizens' preferences align with token house preferences?
    - **Representation**: How representative are different ideologies and experiences in the voter mix?
    - **Evolution**: How should the badgeholder community evolve alongside the wider community of Superchain users and contributors?

    Looking forward, it will be exciting to see how these preferences and voting blocs evolve over future rounds and how projects react to these signals. My hypothesis is that the most successful projects will perform well across multiple metrics rather than optimizing for a single metric. **Sound.xyz** is a good example: it received one of the highest allocations overall despite not topping any single category (and being middle of the pack in terms of gas fees).

    The code and data used for this analysis are available on the [OSO GitHub repository](https://github.com/opensource-observer/insights/tree/main/analysis/optimism/retrofunding4). We welcome collaboration and further exploration of this data.
    """
    )
    return


@app.cell
def _():
    # Color definitions
    COLOR1 = "#FF0420"
    COLOR2 = "#FF6969"
    COLOR3 = "#FFCCDD"

    # Font size definitions
    FONT_SIZE = 15
    TITLE_SIZE = 20
    SUB_SIZE = 11
    return COLOR1, FONT_SIZE, TITLE_SIZE


@app.cell
def _():
    import json
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    import warnings

    warnings.filterwarnings("ignore")
    return go, json, pd


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    client = pyoso.Client()
    pyoso_db_conn = client.dbapi_connection()
    return client, mo


if __name__ == "__main__":
    app.run()
