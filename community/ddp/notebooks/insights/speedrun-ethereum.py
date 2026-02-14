import marimo

__generated_with = "unknown"
app = marimo.App()


@app.cell(hide_code=True)
def _(df_sre_users_all, mo):
    _team = "OSO Team"
    _date = "18 December 2025"

    mo.vstack([
        mo.md(f"""
        # **Case Study: Speedrun Ethereum**
        <small>Author: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">{_team}</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">{_date}</span></small>
        """),
        mo.md("""

        ## Introduction

        We conducted this analysis as part of a broader inquiry into the state of the Ethereum developer ecosystem in 2025, grounded in three working hypotheses:

        1. Developer retention is a leading indicator of ecosystem health and, over time, a meaningful predictor of long-term token price, value accrual, network GDP, etc.

        2. Ethereum’s early open-source culture is eroding as the crypto ecosystem matures, becomes more competitive, and partners with tradfi/web2.

        3. Other ecosystems (eg, AI) have emerged as powerful bottom-up attractors for ambitious, mission-driven developers.

        Using Speedrun Ethereum as a focused case study, the data suggests that bottom-up programs still work. Speedrun Ethereum is successfully counteracting these headwinds by onboarding, retaining, and anchoring net-new developers in the Ethereum ecosystem.

        """),
        mo.accordion({
            "<b>Expand for additional context</b>": mo.accordion({
                "Definitions": f"""
                - **Users**: We only consider the {len(df_sre_users_all):,.0f} developers (out of 17K+ total users) with GitHub profiles saved.
                - **Cohort Month**: We use the profile `createdAt` field in the SRE profile database, rounded to the near month.
                - **Batch ID**: Some though not all developers were assigned a learning batch (group) when they went through the program.
                - **Challenges Completed**: The number of SRE challenges the user successfully completed (according to their profile).
                - **Location**: Where available, the country code of the user.
                - **Forked `scaffold-eth`**: Whether the user has one or more of the [scaffold-eth](https://github.com/scaffold-eth/scaffold-eth-2/forks?include=active&page=1&period=2y&sort_by=last_updated) repos forked to their personal GitHub.
                - **Experience Categories**: *Newb* developers have little to no GitHub activity before joining SRE; *Learning* developers show some prior activity but less than a year; *Experienced* developers have more than 12 months of pre-SRE activity; *Delayed Start* developers first become active only several months after their SRE start date.
                - **Active Month**: Any month with ≥1 qualifying Push or PullRequest event on a public GitHub repo.
                - **Ecosystem Classification**: Repos are classified as *Ethereum*, *Other EVM Chain*, *Personal*, or *Other* based on the Electric Capital ecosystem mappings. It's easy to add more classifications.
                - **Retention**: The share of a cohort that is active at month *t*, normalized at month 0 (the month they created a profile in SRE).
                - **Full-time month**: Any month with more than 10 days of qualifying activity.
                - **Velocity**: The sum over active days of (1 + ln(events per day))
                - **Change Categories**: Average monthly activity changes after SRE compared to before. Categories include *Major Increase* (+100%), *Minor Increase* (+10 to +99%) to *About the Same* (-10% to +10%), *Minor Decrease* (-10% to -50%), and *Major Decrease* (-50%).
                """,
                "Data Sources": """
                - SRE GitHub users (`int_sre_github_users`): SRE user registry, cohorts, batches, challenges
                - GitHub events by user (`int_sre_github_events_by_user`): public GitHub events joined to SRE users, from [GitHub Archive](https://gharchive.org)
                - OpenDevData ecosystem mappings (`stg_opendevdata__*`): Electric Capital's repo → ecosystem mappings, from [Open Dev Data](https://opendevdata.org/)
                """,
                "Further Resources": """
                - [Speedrun Ethereum](https://speedrunethereum.com/)
                - [Getting Started with Pyoso](https://docs.opensource.observer/docs/get-started/python)
                - [Marimo Documentation](https://docs.marimo.io/)
                """
            })
        }),
        mo.md("PS!<br>All of this data is live, public, and interactive. You can also download the code that generates this notebook and run it locally.")
    ])
    return


@app.cell(hide_code=True)
def fetch_data(mo, pyoso_db_conn, stringify):
    df_sre_users_all = mo.sql(
        f"""
        WITH users AS (
          SELECT
            github_handle AS user_name,
            MAX(COALESCE(challenges_completed,0)) AS challenges_completed,
            MIN(batch_id) AS batch_id,
            MIN(created_at) AS start_date,
            MIN_BY(location_code, created_at) AS location_code
          FROM int_sre_github_users
          GROUP BY 1
        )
        SELECT
          user_name,
          challenges_completed,
          batch_id,
          CAST(DATE_TRUNC('MONTH', start_date) AS DATE) AS start_month,
          YEAR(start_date) AS cohort_year,
          location_code
        FROM users
        """,
        output=False,
        engine=pyoso_db_conn
    )

    df_github_events_all = mo.sql(
        f"""
        WITH repo_mapping AS (
          WITH repo_attributes AS (
            SELECT
              r.repo_id,
              e.name AS ecosystem_name,
              er.ecosystem_id AS ecosystem_id,     
              e.is_chain,
              e.is_crypto,
            FROM int_opendevdata__repositories_with_repo_id r
            JOIN stg_opendevdata__ecosystems_repos_recursive er
              ON r.opendevdata_id = er.repo_id
            JOIN stg_opendevdata__ecosystems e
              ON e.id = er.ecosystem_id
          ),
          ecosystem_flags AS (
            SELECT
              repo_id,
              bool_or(ecosystem_name = 'Ethereum' OR ecosystem_name = 'Celo') AS is_ethereum,
              bool_or(ecosystem_name = 'Ethereum Virtual Machine Stack') AS is_evm,
              bool_or(is_chain = 1) AS is_nonevm,
              bool_or(is_crypto = 1) AS is_crypto
            FROM repo_attributes
            GROUP BY 1
          )
          SELECT
            repo_id AS github_repo_id,
            CASE
              WHEN is_ethereum THEN 'Ethereum'
              WHEN is_evm THEN 'Other EVM Chain'
              WHEN is_nonevm THEN 'Non-EVM Chain'
              WHEN is_crypto THEN 'Other (Crypto-Related)'
              ELSE 'Other (Non-Crypto)'
            END AS best_match_ecosystem
          FROM ecosystem_flags
        ),
        monthly_events AS (
          SELECT
            CAST(DATE_TRUNC('MONTH', event_time) AS DATE) AS bucket_month,
            user_name,
            repo_name,
            github_repo_id,
            COUNT(*) AS event_count
          FROM int_sre_github_events_by_user
          WHERE
            event_type IN ('PushEvent', 'PullRequestEvent')
            AND user_name IN ({stringify(df_sre_users_all['user_name'])})
          GROUP BY 1,2,3,4
        )
        SELECT
          bucket_month,
          user_name,
          github_repo_id,
          repo_name,
          CASE
            WHEN best_match_ecosystem IS NOT NULL
              THEN best_match_ecosystem
            WHEN user_name = split_part(repo_name, '/', 1)
              THEN 'Personal'
            ELSE 'Unknown'
          END AS repo_label,
          event_count
        FROM monthly_events
        LEFT JOIN repo_mapping USING (github_repo_id)
        """,
        output=False,
        engine=pyoso_db_conn
    )


    df_github_velocity_all = mo.sql(
        f"""
        WITH daily_activity AS(
          SELECT
            DATE_TRUNC('DAY', event_time) AS bucket_day,
            user_name,
            COUNT(*) AS event_count
          FROM int_sre_github_events_by_user
          WHERE
            event_type IN ('PushEvent', 'PullRequestEvent')
            AND user_name IN ({stringify(df_sre_users_all['user_name'])})
          GROUP BY 1,2
        )

        SELECT
          CAST(DATE_TRUNC('MONTH', bucket_day) AS DATE) AS bucket_month,
          user_name,
          SUM(1 + ln(event_count)) AS velocity
        FROM daily_activity
        GROUP BY 1,2
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return df_github_events_all, df_github_velocity_all, df_sre_users_all


@app.function(hide_code=True)
def build_user_table(df_events):
    cols = ['user_name', 'cohort_year', 'start_month', 'location_code',
            'challenges_completed', 'batch_id', 'dev_forked_scaffold-eth',  
            'first_month_activity', 'last_month_activity', 'months_of_prior_activity', 'experience_category', 'change_category']
    df = df_events[cols].drop_duplicates().reset_index(drop=True).copy()
    df['user_name'] = df['user_name'].apply(lambda x: f'https://github.com/{x}')
    return df


@app.cell(hide_code=True)
def process_data(
    analyze_pre_post_velocity,
    build_user_velocity_grid,
    df_github_events_all,
    df_github_velocity_all,
    df_sre_users_all,
    pd,
):
    df_merged = df_github_events_all.merge(df_sre_users_all, on='user_name')
    df_merged['org_name'] = df_merged.apply(lambda x: 'Personal' if x['repo_label'] == 'Personal' else x['repo_name'].split('/')[0], axis=1)
    df_merged['cohort_year'] = df_merged['cohort_year'].apply(str)
    df_merged['batch_id'] = df_merged['batch_id'].apply(lambda x: '-' if pd.isna(x) else str(int(x)).zfill(2))
    df_merged['month'] = (
        (pd.to_datetime(df_merged['bucket_month']).dt.year - pd.to_datetime(df_merged['start_month']).dt.year)*12
        + (pd.to_datetime(df_merged['bucket_month']).dt.month - pd.to_datetime(df_merged['start_month']).dt.month)
    )
    df_merged['scaffold-eth_fork'] = df_merged.apply(lambda x: "scaffold-eth" in x['repo_name'].split('/')[1] and x['repo_label'] == 'Personal', axis=1)

    _forkers = df_merged[df_merged['scaffold-eth_fork']]['user_name'].unique()
    df_merged['dev_forked_scaffold-eth'] = df_merged['user_name'].isin(_forkers)
    df_merged['activated'] = (df_merged['dev_forked_scaffold-eth']) | (df_merged['batch_id'] != '-') | (df_merged['challenges_completed'] > 0)

    _user_summary = (
        df_merged
        .assign(
            prior_month=lambda d: d['month'].where(d['month'] < 0)
        )
        .groupby('user_name')
        .agg(
            min_month=('month','min'),
            months_of_prior_activity=('prior_month',lambda s: s.nunique()),
            first_month_activity=('bucket_month','min'),
            last_month_activity=('bucket_month','max'),
            start_month=('start_month','min')
        )
    )

    def classify_experience(row):
        if row['min_month'] >= 3:
            return 'Newb' #'Delayed Start'
        m = row['months_of_prior_activity']
        if m > 12:
            return 'Experienced'
        elif m > 3:
            return 'Learning'
        else:
            return 'Newb'

    _user_summary['experience_category'] = _user_summary.apply(classify_experience, axis=1)
    _velocity_grid = build_user_velocity_grid(df_github_velocity_all, df_sre_users_all)
    _user_velocity = analyze_pre_post_velocity(_velocity_grid)

    ecosystem_options = sorted(df_github_events_all['repo_label'].unique())

    df_merged = (
        df_merged.merge(
            _user_summary[['first_month_activity', 'last_month_activity', 'months_of_prior_activity', 'experience_category']],
            left_on='user_name',
            right_index=True,
            how='left'
        ).merge(
            _user_velocity[['user_name', 'change_category']],
            on='user_name',
            how='left'
        )
    )
    return df_merged, ecosystem_options


@app.cell(hide_code=True)
def process_dev_velocity(SRE_BASE, SRE_GREEN, np, pd, px):
    def build_user_velocity_grid(df_velocity, df_users):

        df_velocity = df_velocity.copy()
        df_velocity['bucket_month'] = pd.to_datetime(df_velocity['bucket_month'])

        df_users = df_users[['user_name','start_month']].copy()
        df_users['start_month'] = pd.to_datetime(df_users['start_month'])

        df = df_velocity.merge(df_users, on='user_name', how='left')
        df = df.sort_values(by='bucket_month')

        all_users = df_users['user_name'].to_numpy()
        all_dates = pd.date_range(
            start=df['bucket_month'].min(),
            end=df['bucket_month'].max(),
            freq='MS'
        )
        grid = (
            pd.MultiIndex.from_product(
                [all_users, all_dates],
                names=['user_name','bucket_month']
            ).to_frame(index=False)
        )

        grid = grid.merge(
            df[['user_name','bucket_month','velocity']],
            on=['user_name','bucket_month'],
            how='left'
        )
        grid = grid.merge(df_users, on='user_name', how='left')

        grid['velocity'] = grid['velocity'].fillna(0)
        grid['timing'] = np.where(
            grid['bucket_month'] >= grid['start_month'],
            'post-Speedrun Ethereum',
            'pre-Speedrun Ethereum'
        )

        df_all_velocity = (
            grid
            .groupby(['bucket_month','timing'], as_index=False)['velocity']
            .sum()
        )
        return grid[['user_name', 'bucket_month', 'start_month', 'timing', 'velocity']]

    def analyze_pre_post_velocity(
        grid,
        buffer_months=1,
        comparison_months=6,
        major_ratio=2.0,
        minor_ratio=1.1
    ):
        """
        Given a user-month velocity grid, compute how each developer's
        velocity changes pre/post Speedrun Ethereum.

        Parameters
        ----------
        grid : pd.DataFrame
            Output of build_user_velocity_grid with columns:
            ['user_name','bucket_month','start_month','timing','velocity'].
            Assumed monthly, with missing months filled as velocity = 0.
        buffer_months : int
            Number of months to ignore before and after the start month.
        comparison_months : int
            Number of months in the pre and post comparison windows.
        major_ratio : float
            Ratio threshold for Major Increase/Decrease (e.g., >=2x or <=0.5x).
        minor_ratio : float
            Ratio threshold for Minor Increase/Decrease (e.g., >=1.1x or <=0.9x).

        Returns
        -------
        pd.DataFrame with columns:
            ['user_name','pre_velocity','post_velocity','ratio','change_category']
        """

        g = grid.copy()
        g['bucket_month'] = pd.to_datetime(g['bucket_month'])
        g['start_month'] = pd.to_datetime(g['start_month'])

        g['rel_month'] = (
            (g['bucket_month'].dt.year - g['start_month'].dt.year)*12
            + (g['bucket_month'].dt.month - g['start_month'].dt.month)
        )

        pre_start = -(buffer_months + comparison_months)
        pre_end = -(buffer_months + 1)
        post_start = buffer_months + 1
        post_end = buffer_months + comparison_months

        pre = (
            g[(g['rel_month'] >= pre_start) & (g['rel_month'] <= pre_end)]
            .groupby('user_name', as_index=False)['velocity']
            .mean()
            .rename(columns={'velocity':'pre_velocity'})
        )

        post = (
            g[(g['rel_month'] >= post_start) & (g['rel_month'] <= post_end)]
            .groupby('user_name', as_index=False)['velocity']
            .mean()
            .rename(columns={'velocity':'post_velocity'})
        )

        summary = pre.merge(post, on='user_name', how='outer')

        eps = 1e-9
        summary['ratio'] = summary['post_velocity'] / (summary['pre_velocity'] + eps)

        def categorize(row):
            pre_v = row['pre_velocity']
            post_v = row['post_velocity']
            r = row['ratio']

            if pre_v < eps and post_v < eps:
                return 'About the Same'
            if pre_v < eps and post_v >= eps:
                return 'Major Increase'        
            if pre_v >= eps and post_v < eps:
                return 'Major Decrease'
            if r >= major_ratio:
                return 'Major Increase'
            if r >= minor_ratio:
                return 'Minor Increase'
            if r <= 1/major_ratio:
                return 'Major Decrease'
            if r <= 1/minor_ratio:
                return 'Minor Decrease'
            return 'About the Same'

        summary['change_category'] = summary.apply(categorize, axis=1)
        return summary[['user_name','pre_velocity','post_velocity','ratio','change_category']]

    def developer_activity_area_chart(df_velocity_grid, method='Active Developers'):

        if method == 'Active Developers':
            df = (
                df_velocity_grid
                .groupby(['bucket_month','timing'], as_index=False)['velocity']
                .agg(lambda x: (x > 0).sum())
            )
        elif method == 'Full-time Developers':
            df = (
                df_velocity_grid
                .groupby(['bucket_month','timing'], as_index=False)['velocity']
                .agg(lambda x: (x >= 10).sum())
            )
        else:
            method = 'Velocity'
            df = (
                df_velocity_grid
                .groupby(['bucket_month','timing'], as_index=False)['velocity']
                .sum()
            )

        fig = px.area(
            data_frame=df,
            x='bucket_month',
            y='velocity',
            color='timing',
            line_shape='hvh',
            labels={
                'bucket_month': 'Month',
                'timing': 'Timing',
                'velocity': method
            },
            color_discrete_map={
                'post-Speedrun Ethereum': SRE_GREEN,
                'pre-Speedrun Ethereum': SRE_BASE
            },
        )

        fig.update_layout(
            font=dict(size=12, color="#111"),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=40, l=20, r=20, b=20),
            hovermode='x unified',
            legend=dict(
                orientation="v",
                x=0.01,
                y=1.00,
                xanchor="left",
                yanchor="top"
            ),
        )
        fig.update_xaxes(
            showline=True,
            linewidth=1.5,
            linecolor="black",
            ticks="outside",
            tickwidth=1.5,
            tickcolor="black",
            ticklen=6,
        )
        fig.update_yaxes(
            showline=True,
            linewidth=1.5,
            linecolor="black",
            ticks="outside",
            tickwidth=1.5,
            tickcolor="black",
            ticklen=6,
            rangemode="tozero"
        )
        fig.update_traces(line=dict(width=0.5))
        return fig
    return (
        analyze_pre_post_velocity,
        build_user_velocity_grid,
        developer_activity_area_chart,
    )


@app.cell(hide_code=True)
def reuseable_dropdowns(ecosystem_options, mo):
    def ui_dropdown_activity_metric(value='Active Developers', label='Select a developer metric'):
        return mo.ui.dropdown(
            options=['Active Developers', 'Full-time Developers', 'Velocity'],
            value=value,
            label=label
        )

    def ui_dropdown_experience_select(value='Experienced', label='Select an experience level'):
        return mo.ui.dropdown(
            options=['Experienced', 'Learning', 'Newb'],
            value=value,
            label=label
        )

    def ui_multiselect_ecosystem(value=None, label='Filter ecosystem(s)'):
        if not value:
            value = ecosystem_options
        else:
            value = [value]
        return mo.ui.multiselect(
            options=ecosystem_options,
            value=value,
            label=label
        )
    return (
        ui_dropdown_activity_metric,
        ui_dropdown_experience_select,
        ui_multiselect_ecosystem,
    )


@app.cell(hide_code=True)
def _(ui_dropdown_activity_metric, ui_multiselect_ecosystem):
    activity_select1 = ui_dropdown_activity_metric(label='Analyze')
    ecosystem_select1 = ui_multiselect_ecosystem(value='Ethereum', label='and apply it to the')
    return activity_select1, ecosystem_select1


@app.cell(hide_code=True)
def _(
    activity_select1,
    build_user_velocity_grid,
    developer_activity_area_chart,
    df_github_velocity_all,
    df_merged,
    df_sre_users_all,
    ecosystem_options,
    ecosystem_select1,
    mo,
    show_plotly,
):
    def _chart(labels, activity_metric):
        if not labels:
            labels = ecosystem_options
        _df = df_merged[df_merged['repo_label'].isin(labels)][['bucket_month', 'user_name']].drop_duplicates()
        _df_velocity = _df.merge(df_github_velocity_all, on=['bucket_month', 'user_name'], how='left')
        _df_users = df_sre_users_all[df_sre_users_all['user_name'].isin(_df['user_name'].unique())]
        _activity_grid = build_user_velocity_grid(_df_velocity, _df_users)
        _fig = developer_activity_area_chart(_activity_grid, method=activity_metric)
        return show_plotly(_fig)


    mo.vstack([
        mo.md("---"),
        mo.md("## Speedrun Ethereum has contributed an incremental ~250 monthly active developers to Ethereum"),
        mo.md("_Measured as the increase in Ethereum-active developers attributable to SRE alumni relative to the pre-SRE baseline._"),
        mo.hstack([activity_select1, ecosystem_select1, mo.md("ecosystem(s)")], align='start', justify='start'),
        _chart(labels=ecosystem_select1.value, activity_metric=activity_select1.value),
    ])
    return


@app.cell(hide_code=True)
def _(
    SRE_GREEN,
    SRE_PINK,
    SRE_YELLOW,
    df_merged,
    mo,
    pd,
    px,
    show_plotly,
    show_stat,
):
    _user_table = build_user_table(df_merged)
    _total_devs = _user_table['user_name'].nunique()
    _newb_devs = _user_table[_user_table['experience_category'] == 'Newb']['user_name'].nunique()
    _learning_devs = _user_table[_user_table['experience_category'] == 'Learning']['user_name'].nunique()
    _experienced_devs = _user_table[_user_table['experience_category'] == 'Experienced']['user_name'].nunique()
    _stats = mo.hstack([
        show_stat(value=_total_devs, label='Total Developers', caption="With public commits"),
        show_stat(value=_experienced_devs, label="Experienced Developers", caption="12+ months experience pre-SRE"),
        show_stat(value=_learning_devs, label="Learning Developers", caption="3-12 months experience pre-SRE"),
        show_stat(value=_newb_devs, label="Newb Developers", caption="<3 months experience pre-SRE"),
        ], widths='equal'
    )

    _df = (
        _user_table
        .groupby(['experience_category', 'start_month'], as_index=False)['user_name']
        .nunique()
        .rename(columns={'user_name': 'num_users'})
    )
    _df['start_month'] = pd.to_datetime(_df['start_month'])
    _all_cats = sorted(_df['experience_category'].unique())
    _all_months = pd.date_range(start=_df['start_month'].min(), end=_df['start_month'].max(), freq='MS')
    _grid = (pd.MultiIndex.from_product([_all_cats, _all_months], names=['experience_category', 'start_month']).to_frame(index=False))
    _df = (
        _grid
        .merge(_df, on=['experience_category', 'start_month'], how='left')
        .fillna({'num_users': 0})
        .sort_values(['experience_category', 'start_month'])
    )
    _df['cumsum'] = _df.groupby('experience_category')['num_users'].cumsum()

    _fig = px.bar(
        data_frame=_df,
        x='start_month',
        y='num_users',
        color='experience_category',
        #line_shape='hvh',
        category_orders={'experience_category': ['Experienced', 'Learning', 'Newb']},
        color_discrete_map={
            'Newb': SRE_PINK,
            'Learning': SRE_YELLOW,
            'Experienced': SRE_GREEN
        },
        labels={
            'start_month': 'Start Month',
            'num_users': 'Developers',
            'experience_category': 'Experience Level'
        },
    )
    _fig.update_layout(
        font=dict(size=12, color="#111"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(t=40, l=20, r=20, b=20),
        hovermode='x unified',
        legend=dict(
            orientation="v",
            x=0.01,
            y=1.00,
            xanchor="left",
            yanchor="top"
        )    
    )
    _fig.update_xaxes(
        showline=True,
        linewidth=1.5,
        linecolor="black",
        ticks="outside",
        tickwidth=1.5,
        tickcolor="black",
        ticklen=6,
    )
    _fig.update_yaxes(
        showline=True,
        linewidth=1.5,
        linecolor="black",
        ticks="outside",
        tickwidth=1.5,
        tickcolor="black",
        ticklen=6,
        rangemode="tozero"
    )

    mo.vstack([
        mo.md("---"),
        mo.md(f"""## Of the {_total_devs:,.0f} users with a GitHub handle linked to their profile, the majority started Speedrun Ethereum with little or no prior coding experience"""),
        _stats,
        show_plotly(_fig),
    ])
    return


@app.cell(hide_code=True)
def plotly_sankey(go, np):
    def user_funnel_sankey(df_sre_users):

        df = df_sre_users.copy()
        df['program_status'] = np.where(
            (df['batch_id'] != '-') | (df['challenges_completed'] > 0),
            'In Batch / Completed Challenge',
            'No Formal Program'
        )

        exp_labels = sorted(df['experience_category'].unique().tolist())
        prog_labels = sorted(df['program_status'].unique().tolist())
        change_labels = sorted(df['change_category'].unique().tolist())

        labels = exp_labels + prog_labels + change_labels
        label_to_idx = {label:i for i,label in enumerate(labels)}

        link1 = (
            df
            .groupby(['experience_category','program_status'])['user_name']
            .nunique()
            .reset_index(name='value')
        )
        link2 = (
            df
            .groupby(['program_status','change_category'])['user_name']
            .nunique()
            .reset_index(name='value')
        )

        sources = []
        targets = []
        values = []
        for _, row in link1.iterrows():
            sources.append(label_to_idx[row['experience_category']])
            targets.append(label_to_idx[row['program_status']])
            values.append(row['value'])
        for _, row in link2.iterrows():
            sources.append(label_to_idx[row['program_status']])
            targets.append(label_to_idx[row['change_category']])
            values.append(row['value'])

        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        label=labels,
                        pad=20,
                        thickness=20
                    ),
                    link=dict(
                        source=sources,
                        target=targets,
                        value=values
                    )
                )
            ]
        )

        fig.update_layout(
            font=dict(size=12),
            height=600,
            margin=dict(t=40, l=20, r=20, b=20),
        )
        return fig
    return


@app.cell(hide_code=True)
def _(mo, show_stat):
    def show_developer_stats(df_users):
        _total_devs = df_users['user_name'].nunique()
        _experienced_devs = df_users[df_users['experience_category'] == 'Experienced']['user_name'].nunique()
        _batch_devs = df_users[df_users['batch_id'] != '-']['user_name'].nunique() 
        _challenge_devs = df_users[df_users['challenges_completed']>=1]['user_name'].nunique() 
        _increase_devs = df_users[df_users['change_category'].str.contains('Increase')]['user_name'].nunique() 

        return mo.hstack([
            show_stat(value=_total_devs, label='Total Developers', caption="With public commits"),
            show_stat(value=_experienced_devs, label="Experienced Developers", caption="12+ months experience pre-SRE"),
            show_stat(value=_batch_devs, label="Assigned Learning Batch", caption="With batch IDs"),
            show_stat(value=_challenge_devs, label="Completed Challenges", caption="With 1+ challenge"),
            show_stat(value=_increase_devs, label="Increased Dev Activity", caption="After SRE")
        ], widths='equal')
    return


@app.cell(hide_code=True)
def _(
    SRE_GREEN,
    SRE_PINK,
    SRE_YELLOW,
    ecosystem_options,
    go,
    make_subplots,
    math,
    pd,
):
    def experience_metrics(df_merged, repo_labels=ecosystem_options, n_months=3):

        # Target ecosystem contribution universe
        df = df_merged[
            (df_merged['activated'])
            & (df_merged['month'] > 0)
            & (df_merged['repo_label'].isin(repo_labels))
        ].copy()

        this_p = pd.to_datetime(df['bucket_month'].max()).to_period('M')
        cutoff_p = this_p - (n_months - 1)

        u = (
            df.assign(
                start_p=pd.to_datetime(df['start_month'], errors='coerce').dt.to_period('M'),
                bucket_p=pd.to_datetime(df['bucket_month'], errors='coerce').dt.to_period('M'),
            )
            .groupby('user_name', as_index=False)
            .agg(
                experience_category=('experience_category', 'first'),
                start_p=('start_p', 'min'),
                active_months=('bucket_p', 'nunique'),
                last_bucket_p=('bucket_p', 'max'),
                event_count=('event_count', 'sum')
            )
        )

        start_pi = pd.PeriodIndex(u['start_p'], freq='M')
        u['months_since_start'] = this_p.ordinal - start_pi.astype('int64')
        u['eligible_months'] = (u['months_since_start'] + 1).clip(lower=1)
        u['share_months'] = u['active_months'] / u['eligible_months'] * 100
        u['active_last_n_months'] = (u['last_bucket_p'] >= cutoff_p).astype('int64')

        out = (
            u.groupby('experience_category')
             .agg(
                 **{
                     # rename: this is "contributed to target ecosystem(s)"
                     'Contributed to Target Ecosystem(s)': ('user_name', 'nunique'),
                     f'Active in Last {n_months} Months': ('active_last_n_months', 'sum'),
                     'Total Active Months': ('active_months', 'sum'),
                     'Avg. Months Since Starting SRE': ('months_since_start', 'mean'),
                     'Share of Months With Activity': ('share_months', 'mean'),
                     'Total PRs/Push Events': ('event_count', 'sum')
                 }
             )
            .apply(lambda x: round(x,1))
            .reset_index()
        )

        # Global denominators (All)
        signed_up = (
            df_merged.groupby('experience_category', as_index=False)['user_name']
            .nunique()
            .rename(columns={'user_name': 'Signed Up for SRE (All)'})
        )

        performed_all = (
            df_merged[df_merged['activated']]
            .groupby('experience_category', as_index=False)['user_name']
            .nunique()
            .rename(columns={'user_name': 'Performed 1+ Challenge (All)'})
        )

        out = (
            signed_up
            .merge(performed_all, on='experience_category', how='left')
            .merge(out, on='experience_category', how='left')
            .fillna(0)
            .rename(columns={'experience_category': 'Experience Level'})
        )

        return out

    def experience_facet_funnels(out, n_months=6, cols=3, height_per_row=260):
        df = out.copy()

        stages = [
            'Signed Up for SRE (All)',
            'Performed 1+ Challenge (All)',
            'Contributed to Target Ecosystem(s)',
            f'Active in Last {n_months} Months',
        ]
        stages = [s for s in stages if s in df.columns]
        for s in stages:
            df[s] = pd.to_numeric(df[s], errors='coerce').fillna(0)

        x_max = df[stages].to_numpy().max() * 1.10

        cats = df['Experience Level'].tolist()
        n = len(cats)
        rows = math.ceil(n / cols)

        color_discrete_map= {
            'Newb': SRE_PINK,
            'Learning': SRE_YELLOW,
            'Experienced': SRE_GREEN
        }
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=cats,
            shared_xaxes=False,
            vertical_spacing=0.10,
            horizontal_spacing=0.02,
        )
        fig.update_xaxes(
            showline=True, linewidth=1.5, linecolor="black",
            ticks="outside", tickwidth=1.5, tickcolor="black", ticklen=6,
            range=[0, x_max],
        )
        fig.update_yaxes(
            showline=True, linewidth=1.5, linecolor="black",
            ticks="outside", tickwidth=1.5, tickcolor="black", ticklen=6,
            autorange="reversed",
        )

        for i, cat in enumerate(cats):
            r = i // cols + 1
            c = i % cols + 1
            row = df[df['Experience Level'] == cat].iloc[0]

            x = [row[s] for s in stages]
            y = stages
            bar_color = color_discrete_map.get(cat, "#666")

            fig.add_trace(
                go.Bar(
                    x=x,
                    y=y,
                    marker_color=bar_color,
                    orientation="h",
                    text=[f"{int(v):,}" for v in x],
                    textposition="outside",
                    hovertemplate="%{y}<br>%{x:,}<extra></extra>",
                    showlegend=False,
                ),
                row=r,
                col=c,
            )
            if c > 1:
                fig.update_yaxes(
                    showticklabels=False,
                    ticks="",
                    row=r,
                    col=c,
                )

        fig.update_layout(
            height=rows * height_per_row,
            margin=dict(t=20, l=20, r=50, b=20),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(size=12, color="#111"),
        )

        return fig
    return experience_facet_funnels, experience_metrics


@app.cell(hide_code=True)
def _(ui_multiselect_ecosystem):
    ecosystem_options_funnel = ui_multiselect_ecosystem(label='Select one or more ecosystem(s) to analyze', value='Ethereum')
    return (ecosystem_options_funnel,)


@app.cell(hide_code=True)
def _(
    df_merged,
    ecosystem_options_funnel,
    experience_facet_funnels,
    experience_metrics,
    mo,
    show_plotly,
    show_table,
):
    def _chart(ecosystems):
        _df = experience_metrics(df_merged, repo_labels=ecosystems, n_months=6)
        _fig = experience_facet_funnels(_df, n_months=6, cols=3)
        return mo.vstack([
            show_plotly(_fig),
            mo.md("The table below provides additional detail on the developer funnel:"),
            show_table(_df)
        ])

    mo.vstack([
        mo.md("## Not surprisingly, less experienced developers have higher churn and less overall long-term impact on Ethereum"),
        ecosystem_options_funnel,
        _chart(ecosystem_options_funnel.value)
    ])
    return


@app.cell(hide_code=True)
def _(SRE_GREEN, SRE_PINK, SRE_YELLOW, ecosystem_options, px):
    def experience_retention_line_chart(
        df_merged,
        ecosystems=None,
        max_month=12,
        cohort_years=['2021','2022','2023','2024'],
        cohort_col='experience_category'
    ):

        if not ecosystems:
            ecosystems = ecosystem_options

        df = df_merged[(
            (df_merged['activated'])
            & (df_merged['cohort_year'].isin(cohort_years))
            & (df_merged['month'].between(0,max_month))
            & (df_merged['repo_label'].isin(ecosystems))
        )].copy()

        retention = (
            df
            .groupby(['month', cohort_col], as_index=False)['user_name']
            .nunique()
        )
        cohort_sizes = (
            df
            .groupby(cohort_col)['user_name']
            .nunique()
            .rename('cohort_size')
            .reset_index()
        )
        df = retention.merge(cohort_sizes, on=[cohort_col])
        df['retention_pct'] = (df['user_name'] / df['cohort_size']) * 100

        fig = px.line(
            data_frame=df,
            x='month',
            y='retention_pct',
            color=cohort_col,
            labels={'month': 'Months Since Starting SRE', 'retention_pct': 'Percent of all developers', cohort_col: 'Experience Level'},
            category_orders={cohort_col: ['Experienced', 'Learning', 'Newb']},
            color_discrete_map={
                'Newb': SRE_PINK,
                'Learning': SRE_YELLOW,
                'Experienced': SRE_GREEN
            },
            #line_shape='hvh'
        )
        fig.update_layout(
            font=dict(size=12, color="#111"),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=40, l=20, r=20, b=20),
            hovermode='x unified',
            legend=dict(
                orientation="v",
                x=1.00,
                y=1.00,
                xanchor="right",
                yanchor="top"
            ),
        )
        fig.update_xaxes(
            showline=True,
            linewidth=1.5,
            linecolor="black",
            ticks="outside",
            tickwidth=1.5,
            tickcolor="black",
            ticklen=6,
            dtick=1
        )
        fig.update_yaxes(
            showline=True,
            linewidth=1.5,
            linecolor="black",
            ticks="outside",
            tickwidth=1.5,
            tickcolor="black",
            ticklen=6,
            rangemode="tozero"
        )
        fig.update_traces(line=dict(width=3))
        return fig


    def cohort_year_retention_line_chart(
        df_merged,
        ecosystems=None,
        max_month=12,
        cohort_years=['2022','2023','2024'],
        cohort_col='cohort_year',
        experience_category='Experienced'
    ):

        if not ecosystems:
            ecosystems = ecosystem_options

        df = df_merged[(
            (df_merged['activated'])
            & (df_merged['cohort_year'].isin(cohort_years))
            & (df_merged['experience_category'] == experience_category)
            & (df_merged['month'].between(0,max_month))
            & (df_merged['repo_label'].isin(ecosystems))
        )].copy()

        retention = (
            df
            .groupby(['month', cohort_col], as_index=False)['user_name']
            .nunique()
        )
        cohort_sizes = (
            df
            .groupby(cohort_col)['user_name']
            .nunique()
            .rename('cohort_size')
            .reset_index()
        )
        df = retention.merge(cohort_sizes, on=[cohort_col])
        df['retention_pct'] = (df['user_name'] / df['cohort_size']) * 100

        fig = px.line(
            data_frame=df,
            x='month',
            y='retention_pct',
            color=cohort_col,
            labels={'month': 'Months Since Starting SRE', 'retention_pct': 'Percent of all developers', cohort_col: 'Cohort Year'},
            category_orders={cohort_col: ['2022', '2023', '2024']},
            color_discrete_map={
                '2024': SRE_PINK,
                '2023': SRE_YELLOW,
                '2022': SRE_GREEN
            },
            #line_shape='hvh'
        )
        fig.update_layout(
            font=dict(size=12, color="#111"),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=40, l=20, r=20, b=20),
            hovermode='x unified',
            legend=dict(
                orientation="v",
                x=1.00,
                y=1.00,
                xanchor="right",
                yanchor="top"
            ),
        )
        fig.update_xaxes(
            showline=True,
            linewidth=1.5,
            linecolor="black",
            ticks="outside",
            tickwidth=1.5,
            tickcolor="black",
            ticklen=6,
            dtick=1
        )
        fig.update_yaxes(
            showline=True,
            linewidth=1.5,
            linecolor="black",
            ticks="outside",
            tickwidth=1.5,
            tickcolor="black",
            ticklen=6,
            rangemode="tozero"
        )
        fig.update_traces(line=dict(width=3))
        return fig    
    return cohort_year_retention_line_chart, experience_retention_line_chart


@app.cell(hide_code=True)
def _(ui_multiselect_ecosystem):
    ecosystem_select2 = ui_multiselect_ecosystem(value='Ethereum', label='Share of developers contributing to one or more repos in the')
    return (ecosystem_select2,)


@app.cell(hide_code=True)
def _(
    df_merged,
    ecosystem_select2,
    experience_retention_line_chart,
    mo,
    show_plotly,
):
    mo.vstack([
        mo.md("---"),
        mo.md("## Developers with > 12 months prior experience remain active contributors to Ethereum at significantly higher rates"),
        mo.hstack([ecosystem_select2, mo.md("ecosystem since starting SRE")], justify='start', align='start'),
        show_plotly(
            experience_retention_line_chart(
                df_merged,
                max_month=12,
                ecosystems=ecosystem_select2.value
            )
        ),
    ])
    return


@app.cell(hide_code=True)
def _(
    ui_dropdown_activity_metric,
    ui_dropdown_experience_select,
    ui_multiselect_ecosystem,
):
    activity_select3 = ui_dropdown_activity_metric(value='Active Developers', label='Analyze')
    ecosystem_select3 = ui_multiselect_ecosystem(value='Ethereum', label='in the')
    experience_select3 = ui_dropdown_experience_select(value='Experienced', label='ecosystem(s) for developer who were')
    return activity_select3, ecosystem_select3, experience_select3


@app.cell(hide_code=True)
def _(
    activity_select3,
    build_user_velocity_grid,
    developer_activity_area_chart,
    df_github_velocity_all,
    df_merged,
    df_sre_users_all,
    ecosystem_options,
    ecosystem_select3,
    experience_select3,
    mo,
    show_plotly,
):
    def _chart(labels, experience_level, activity_metric):

        if not labels:
            labels = ecosystem_options

        _df_target = df_merged[
            (df_merged['repo_label'].isin(labels)) 
          & (df_merged['experience_category'] == experience_level)
        ].copy()

        _df = _df_target[['bucket_month', 'user_name']].drop_duplicates()
        _df_velocity = _df.merge(df_github_velocity_all, on=['bucket_month', 'user_name'], how='left')
        _df_users = df_sre_users_all[df_sre_users_all['user_name'].isin(_df['user_name'].unique())]
        _activity_grid = build_user_velocity_grid(_df_velocity, _df_users)
        _fig = developer_activity_area_chart(_activity_grid, method=activity_metric)

        # _df_monthly = build_repo_label_monthly_time(_df_target[_df_target['cohort_year'] != '2025'], month_limit=12)
        # _fig_retention_bar = cohort_retention_bar_chart(_df_monthly)
        # return show_plotly(_fig_retention_bar)
        return show_plotly(_fig)


    mo.vstack([
        mo.md("---"),
        mo.md("## For experienced developers, Speedrun Ethereum functions less as onboarding and more as activation and redirection toward Ethereum"),
        mo.hstack([activity_select3, ecosystem_select3, experience_select3,mo.md("at the time they started SRE")], align='start', justify='start'),
        _chart(labels=ecosystem_select3.value, experience_level=experience_select3.value, activity_metric=activity_select3.value),
    ])
    return


@app.cell(hide_code=True)
def _(ui_dropdown_experience_select, ui_multiselect_ecosystem):
    experience_select4 = ui_dropdown_experience_select(value='Experienced', label='Share of')
    ecosystem_select4 = ui_multiselect_ecosystem(value='Ethereum', label='developers contributing to one or more repos in the')
    return ecosystem_select4, experience_select4


@app.cell(hide_code=True)
def _(
    cohort_year_retention_line_chart,
    df_merged,
    ecosystem_select4,
    experience_select4,
    mo,
    show_plotly,
):
    mo.vstack([
        mo.md("---"),
        mo.md("## Engagement past the 3–month mark is a good predictor of longer-term retention"),
        mo.hstack([experience_select4, ecosystem_select4, mo.md("ecosystem since starting SRE")], justify='start', align='start'),
        show_plotly(
            cohort_year_retention_line_chart(
                df_merged,
                max_month=12,
                ecosystems=ecosystem_select4.value,
                experience_category=experience_select4.value
            )
        ),
    ])
    return


@app.cell(hide_code=True)
def _(
    build_user_velocity_grid,
    df_github_velocity_all,
    df_merged,
    df_sre_users_all,
    mo,
    np,
    pd,
    px,
    show_plotly,
    show_stat,
):
    _repo_order = {
        'Ethereum': 1,
        'Other EVM Chain': 2,
        'Non-EVM Chain': 3,
        'Other (Crypto-Related)': 4,
        'Other (Non-Crypto)': 5,
        'Personal': 6,
        'Unknown': 7,
    }

    _user_table = build_user_table(df_merged[df_merged['repo_label'] == 'Ethereum'])
    _activity_grid = build_user_velocity_grid(df_github_velocity_all, df_sre_users_all)

    _cols = ['bucket_month', 'month', 'user_name', 'org_name', 'repo_name', 'repo_label']
    _df = df_merged[_cols].drop_duplicates().copy()

    _counts =_df.groupby(['org_name', 'repo_label']).size().rename('n').reset_index()
    _counts['repo_order'] = _counts['repo_label'].map(_repo_order).fillna(99).astype(int)
    _counts['score'] = _counts['n'] * 1000 - _counts['repo_order']
    _owner = (
        _counts.loc[_counts.groupby('org_name')['score'].idxmax(), ['org_name', 'repo_label']]
               .rename(columns={'repo_label': 'owner_min'})
    )
    _df = _df.merge(_owner, on='org_name', how='left')
    _df['repo_label_updated'] = np.where(
        _df['repo_label'].eq('Unknown'),
        _df['owner_min'],
        _df['repo_label']
    )
    _overrides = ['defillama', 'cyfrin', 'patrickalphac','sporkdaoofficial', 'ethereum-lists', 'rotki/rotki', 'wslyvh/useweb3', 'consensys-academy-github-classroom', 'risc0', 'raid-guild', 'trailofbits']
    _pattern = '|'.join(map(repr, _overrides)).replace("'", "")
    _df['repo_label_updated'] = np.where(
        _df['repo_name'].str.contains(_pattern, case=False, na=False),
        'Ethereum',
        _df['repo_label_updated']
    )

    _df.drop(columns=['owner_min'], inplace=True)
    _df['repo_order_updated'] = _df['repo_label_updated'].map(_repo_order)

    #_df[_df['repo_label_updated'] == 'Other Ecosystem'].groupby(['org_name'])['user_name'].nunique()

    _key = ['bucket_month', 'month', 'user_name']

    _min_label = (
        _df.loc[_df.groupby(_key)['repo_order_updated'].idxmin(), _key + ['repo_label_updated', 'repo_order_updated']]
        .rename(columns={
            'repo_label_updated': 'min_repo_label_updated',
            'repo_order_updated': 'min_repo_order_updated',
        })
    )

    _df = _min_label.groupby(['min_repo_label_updated', 'bucket_month'], as_index=False)['user_name'].nunique()

    _fig = px.area(
        data_frame=_df,
        x='bucket_month',
        y='user_name',
        color='min_repo_label_updated',
        line_shape='hvh',
        category_orders={'min_repo_label_updated': ['Unknown', 'Other (Non-Crypto)',  'Other (Crypto-Related)',  'Non-EVM Chain', 'Other EVM Chain', 'Ethereum', 'Personal']},
        labels={
            'bucket_month': 'Month',
            'user_name': 'Active Developers',
            'min_repo_label_updated': 'Ecosystem'
        },
    )
    _fig.update_layout(
        font=dict(size=12, color="#111"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(t=40, l=20, r=20, b=20),
        hovermode='x unified',
        legend=dict(
            orientation="v",
            x=0.01,
            y=1.00,
            xanchor="left",
            yanchor="top"
        )
    )
    _fig.update_xaxes(
        showline=True,
        linewidth=1.5,
        linecolor="black",
        ticks="outside",
        tickwidth=1.5,
        tickcolor="black",
        ticklen=6,
    )
    _fig.update_yaxes(
        showline=True,
        linewidth=1.5,
        linecolor="black",
        ticks="outside",
        tickwidth=1.5,
        tickcolor="black",
        ticklen=6,
        rangemode="tozero"
    )

    _tmp = _df.copy()
    _tmp['bucket_month'] = pd.to_datetime(_tmp['bucket_month'])
    _win_2324 = (_tmp['bucket_month'].dt.year.isin([2023, 2024]))
    _win_2021 = (_tmp['bucket_month'].dt.year.isin([2020, 2021]))

    def mean_monthly(label, mask):
        s = _tmp.loc[mask & (_tmp['min_repo_label_updated'] == label), 'user_name']
        return float(s.mean()) if len(s) else 0.0

    def mean_monthly_total(mask):
        s = (
            _tmp.loc[mask]
               .groupby('bucket_month', as_index=False)['user_name']
               .sum()['user_name']
        )
        return float(s.mean()) if len(s) else 0.0

    _total_2324 = mean_monthly_total(_win_2324)
    _total_2021 = mean_monthly_total(_win_2021)

    _eth_2324 = mean_monthly('Ethereum', _win_2324)
    _eth_2021 = mean_monthly('Ethereum', _win_2021)

    _other_evm_2324 = mean_monthly('Other EVM Chain', _win_2324)
    _other_evm_2021 = mean_monthly('Other EVM Chain', _win_2021)

    _other_eco_2324 = mean_monthly('Non-EVM Chain', _win_2324)
    _other_eco_2021 = mean_monthly('Non-EVM Chain', _win_2021)

    _personal_2324 = mean_monthly('Personal', _win_2324)
    _personal_2021 = mean_monthly('Personal', _win_2021)

    _total_delta = _total_2324 - _total_2021
    _eth_delta = _eth_2324 - _eth_2021
    _other_evm_delta = _other_evm_2324 - _other_evm_2021
    _other_eco_delta = _other_eco_2324 - _other_eco_2021
    _personal_delta = _personal_2324 - _personal_2021

    _stats = mo.hstack([
        show_stat(value=_total_2324, label='Avg Active Devs (2023/24)', caption=f"{_total_delta:+.0f} vs 2020/21", format="int"),
        show_stat(value=_personal_2324, label='Avg "Personal Repo Only" Devs (2023/24)', caption=f"{_personal_delta:+.0f} vs 2020/21", format="int"),
        show_stat(value=_eth_2324, label='Avg Ethereum Devs (2023/24)', caption=f"{_eth_delta:+.0f} vs 2020/21", format="int"),
        show_stat(value=_other_evm_2324, label='Avg Other EVM Chain Devs (2023/24)', caption=f"{_other_evm_delta:+.0f} vs 2020/21", format="int"),
        show_stat(value=_other_eco_2324, label='Avg Non-EVM Chain Devs (2023/24)', caption=f"{_other_eco_delta:+.0f} vs 2020/21", format="int"),

    ], widths='equal')

    mo.vstack([
        mo.md("---"),
        mo.md("## Most post-program activity remains concentrated in Ethereum and Ethereum-adjacent personal projects."),
        mo.md("_Personal repos often include early-stage Ethereum experimentation and proto-projects not yet migrated to org-owned repos._"),
        _stats,
        show_plotly(_fig),
    ])

    return


@app.cell(hide_code=True)
def _(df_merged, mo, ui_dropdown_experience_select, ui_multiselect_ecosystem):
    where_now_experience = ui_dropdown_experience_select(label='', value='Experienced')
    change_categories = sorted(df_merged['change_category'].unique())
    where_now_change = mo.ui.multiselect(options=change_categories, value=change_categories, label='')
    where_now_labels = ui_multiselect_ecosystem(label='', value='Ethereum')
    where_now_months = mo.ui.number(value=3, start=1, stop=12, step=1, label='' )
    where_now_direction = mo.ui.dropdown(value='After', options=['Before', 'After'], label='')
    return (
        change_categories,
        where_now_change,
        where_now_direction,
        where_now_experience,
        where_now_labels,
        where_now_months,
    )


@app.function(hide_code=True)
def where_now_user_table(
    df_merged,
    repo_labels,
    experience_categories,
    change_categories,
    month_threshold,
    min_active_months=6,
    min_devs_per_org=1,
):

    df = df_merged[
        (df_merged['repo_label'].isin(list(repo_labels)))
        & (df_merged['experience_category'].isin(list(experience_categories)))
        & (df_merged['change_category'].isin(list(change_categories)))
    ].copy()

    if month_threshold < 0:
        df = df[df['month'] <= month_threshold]
    else:
        df = df[df['month'] >= month_threshold]

    user_table = (
        df.groupby(['org_name', 'user_name', 'experience_category', 'change_category'], as_index=False)
          .agg(active_months=('bucket_month', 'nunique'))
    )
    user_table = user_table[user_table['active_months'] >= int(min_active_months)]

    org_counts = user_table.groupby('org_name')['user_name'].nunique()
    keep_orgs = org_counts[org_counts >= int(min_devs_per_org)].index
    user_table = user_table[user_table['org_name'].isin(keep_orgs)].copy()

    return user_table.reset_index(drop=True)


@app.cell(hide_code=True)
def _(go):
    from wordcloud import WordCloud
    import matplotlib as mpl
    import matplotlib.colors as mcolors

    import base64
    from io import BytesIO
    from PIL import Image

    def pil_to_data_uri(pil_img, fmt="PNG"):
        buf = BytesIO()
        pil_img.save(buf, format=fmt)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/{fmt.lower()};base64,{b64}"

    def plotly_org_wordcloud(
        user_table,
        org_col="org_name",
        user_col="user_name",
        change_col="change_category",
        width=1200,
        height=650,
        max_words=250,
        background_color="white",
        colormap='RdYlGn'
    ):
        df = user_table.copy()

        change_to_score = {
            "Major Increase": 1.0,
            "Major Decrease": -1.0,
            "Minor Increase": 0.5,
            "Minor Decrease": -0.5,
            "No Change": 0.0,
            "Same": 0.0,
            "Neutral": 0.0,
        }

        df["_score"] = df[change_col].map(change_to_score).astype("float64")
        df["_abs_score"] = df["_score"].abs()
        devs = (
            df.sort_values("_abs_score", ascending=False)
              .drop_duplicates([org_col, user_col])
              .loc[:, [org_col, user_col, "_score"]]
              .copy()
        )

        org_dev_counts = devs.groupby(org_col)[user_col].nunique()
        org_mean_score = devs.groupby(org_col)["_score"].mean().clip(-1, 1)

        freqs = (
            org_dev_counts.sort_values(ascending=False)
            .head(max_words)
            .to_dict()
        )

        if not freqs:
            fig = go.Figure()
            fig.update_layout(
                paper_bgcolor="white",
                plot_bgcolor="white",
                margin=dict(t=0, l=0, r=0, b=0),
            )
            fig.update_xaxes(visible=False)
            fig.update_yaxes(visible=False)
            return fig

        cmap = mpl.colormaps[colormap]
        norm = mcolors.Normalize(vmin=-1, vmax=1)

        top_orgs = set(freqs.keys())
        word_to_color = {}
        for org in top_orgs:
            score = float(org_mean_score.get(org, 0.0))
            rgba = cmap(norm(score))
            word_to_color[org] = mcolors.to_hex(rgba, keep_alpha=False)

        def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
            return word_to_color.get(word, "#777777")

        render_scale = 2
        wc = WordCloud(
            width=width * render_scale,
            height=height * render_scale,
            max_words=max_words,
            background_color=background_color,
            prefer_horizontal=0.9,
            collocations=False,
            color_func=color_func,
            contour_width=10,
            contour_color="black",
        ).generate_from_frequencies(freqs)

        pil_img = wc.to_image().resize((width, height), resample=Image.LANCZOS)
        src = pil_to_data_uri(pil_img)

        fig = go.Figure()
        fig.add_layout_image(
            dict(
                source=src,
                xref="x",
                yref="y",
                x=0,
                y=1,
                sizex=1,
                sizey=1,
                sizing="stretch",
                layer="below",
            )
        )

        fig.update_xaxes(visible=False, range=[0, 1])
        fig.update_yaxes(visible=False, range=[0, 1])
        fig.update_layout(
            autosize=True,
            height=height,
            margin=dict(t=60, l=10, r=10, b=10),
            paper_bgcolor="white",
            plot_bgcolor="white",
        )
        return fig
    return (plotly_org_wordcloud,)


@app.cell(hide_code=True)
def _(
    change_categories,
    df_merged,
    ecosystem_options,
    mo,
    plotly_org_wordcloud,
    show_plotly,
    where_now_change,
    where_now_direction,
    where_now_experience,
    where_now_labels,
    where_now_months,
):
    def _chart(repo_labels, experience_cat, change_cats, num_months, direction):
        month_threshold = -num_months if direction == 'Before' else num_months
        if not repo_labels:
            repo_labels = ecosystem_options
        if not change_cats:
            change_cats = change_categories

        user_table = where_now_user_table(
            df_merged=df_merged,
            repo_labels=repo_labels,
            experience_categories=[experience_cat],
            change_categories=change_cats,
            month_threshold=month_threshold,
        )
        wc = plotly_org_wordcloud(user_table, colormap='RdYlGn')
        return show_plotly(wc)

    mo.vstack([
        mo.md("---"),
        mo.md("## SRE developers have gone on to contribute regularly to many different organizations"),
        mo.hstack([
            mo.md("Where"), where_now_experience, mo.md("developers who have"),
            where_now_change, mo.md("activity in the"), where_now_labels, mo.md("ecosystem(s) since SRE were at least"),
            where_now_months, mo.md("months"), where_now_direction, mo.md("starting the program")], align='start', justify='start'),
        _chart(
            repo_labels=where_now_labels.value,
            experience_cat=where_now_experience.value,
            change_cats=where_now_change.value,
            num_months=where_now_months.value,
            direction=where_now_direction.value
        )
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ---

    ## Suggested recommendations

    - **Maintain broad onboarding as a public good**. Continue serving new developers at scale to expand the Ethereum ecosystem and sustain long-term growth.

    - **Prioritize experienced developers as the highest-leverage cohort**. The marginal return on program investment is likely highest when accelerating experienced developers through the first 3–4 months and supporting their transition into steady Ethereum work.

    - **Introduce structured acceleration during the critical early window**. Focus on targeted interventions for experienced developers—such as office hours, mentorship, and opportunities to demo work—to improve conversion and reduce early churn.

    - **Improve visibility into post-program pathways for experienced developers**. Systematically learn what experienced participants want to do next (e.g., join existing teams, launch new projects, pursue side work) and align support accordingly.

    - **Expand the activation funnel to high-intent participants**. Engage the 10K+ developers who have forked, starred, or otherwise interacted with Speedrun Ethereum as a follow-on activation pool for developers who already demonstrate interest and intent.
    """
    )
    return


@app.cell(hide_code=True)
def _():
    # Code snippets
    return


@app.cell(hide_code=True)
def ui_funcs(mo):
    def show_stat(value, label, caption="", format="int"):
        if format == "int": value_str = f"{value:,.0f}"
        elif format == "1f": value_str = f"{value:,.1f}"
        elif format == "pct": value_str = f"{value:.1f}%"
        else: value_str = str(value)
        return mo.stat(value=value_str, label=label, caption=caption, bordered=True)

    def show_plotly(fig):
        return mo.ui.plotly(figure=fig, config={'displayModeBar': False})

    def show_table(dataframe, **kwargs):
        return mo.ui.table(dataframe.reset_index(drop=True), show_column_summaries=False, show_data_types=False, **kwargs)
    return show_plotly, show_stat, show_table


@app.cell(hide_code=True)
def _():
    SRE_GREEN = '#026262'
    SRE_BASE  = '#e5e7eb'

    SRE_PINK = '#E4D0FF'
    SRE_TEAL = '#8CD9DA'
    SRE_YELLOW = '#FBCB83'
    return SRE_BASE, SRE_GREEN, SRE_PINK, SRE_YELLOW


@app.cell(hide_code=True)
def _():
    stringify = lambda arr: "'" + "','".join(arr) + "'"
    return (stringify,)


@app.cell(hide_code=True)
def imports():
    from datetime import datetime
    import math
    import numpy as np
    import pandas as pd

    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    return go, make_subplots, math, np, pd, px


@app.cell(hide_code=True)
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
