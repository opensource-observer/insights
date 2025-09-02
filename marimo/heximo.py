import marimo

__generated_with = "0.15.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""See [Open Source Observer's docs](https://docs.opensource.observer/docs/) for more guidance on how to get access to raw and processed data.""")
    return


@app.cell
def _():
    from dotenv import load_dotenv
    import marimo as mo
    import os
    import datetime
    import numpy as np
    import plotly.express as px
    import pandas as pd
    from pandas.tseries.offsets import MonthBegin
    from pyoso import Client    

    load_dotenv()
    OSO_API_KEY = os.environ['OSO_API_KEY']
    client = Client(api_key=OSO_API_KEY)
    stringify = lambda arr: "'" + "','".join(arr) + "'"
    return client, mo, np, pd, px, stringify


@app.cell
def _():
    START_DATE = '2022-01-01'
    END_DATE   = '2025-07-31'

    CHAINS = [
        'ARENAZ','AUTOMATA','BASE','BOB','CYBER','FRAX','HAM','INK','KROMA',
        'LISK','LYRA','METAL','MINT','MODE','OPTIMISM','ORDERLY','POLYNOMIAL',
        'RACE','REDSTONE','SHAPE','SONEIUM','SWAN','SWELL','UNICHAIN',
        'WORLDCHAIN','XTERIO','ZORA'
    ]

    TVL_METRIC = 'DefiLlama TVL (USD)'
    FEES_METRIC = 'Fees Paid (ETH)'
    TX_METRIC = 'Transaction Count'

    GC_MECHANISM_NAME = 'Grants Council'
    RF_MECHANISM_NAME = 'Retro Funding'

    REFRESH = True
    return (
        CHAINS,
        END_DATE,
        FEES_METRIC,
        GC_MECHANISM_NAME,
        REFRESH,
        RF_MECHANISM_NAME,
        START_DATE,
        TVL_METRIC,
        TX_METRIC,
    )


@app.cell
def _():
    SOURCE_NAMES  = ['Github', 'Optimism', 'Base',    'Mode', 'Worldchain', 'Soneium', 'Ink',     'Unichain', 'Zora', 'Others']
    SOURCE_COLORS = ['#104C35', '#ff0420', '#0052FF', '#DFFE00', '#FF6F0F', '#57F8FE', '#7132F5',  '#FF007A', 'indigo', '#aaa']
    SOURCE_PALETTE = dict(zip(SOURCE_NAMES, SOURCE_COLORS))
    return SOURCE_NAMES, SOURCE_PALETTE


@app.cell
def _(pd):
    gcp_query = """
    SELECT
      dt,
      CASE
        WHEN chain = 'op' THEN 'OPTIMISM'
        WHEN chain = 'fraxtal' THEN 'FRAX'
        ELSE UPPER(chain)
      END AS chain,
      receipt_status,
      APPROX_COUNT_DISTINCT(`hash`) AS tx_count,
      SUM(receipt_gas_used / 1e18 * receipt_effective_gas_price) as l2_fees,
      SUM(receipt_l1_fee / 1e18) AS l1_fees
    FROM `optimism_superchain_raw_onchain_data.transactions`
    WHERE dt > '2021-01-01'
    GROUP BY 1,2,3
    ORDER BY 1,2,3
    """

    def collective_revenue(chain, l2_fees):
        if chain == 'Optimism':
            return l2_fees
        elif chain == 'Celo':
            return 0
        else:
            return l2_fees * 0.15

    df_gas_by_chain = pd.read_csv("marimo/gasfees.csv")
    df_gas_by_chain['sample_date'] = pd.to_datetime(df_gas_by_chain['dt'])
    df_gas_by_chain['chain'] = df_gas_by_chain['chain'].apply(lambda x: x.title())
    df_gas_by_chain['collective_revenue'] = df_gas_by_chain.apply(lambda row: collective_revenue(row['chain'], row['l2_fees']), axis=1)

    df_gas_by_chain
    return (df_gas_by_chain,)


@app.cell
def _(
    CHAINS,
    END_DATE,
    FEES_METRIC,
    REFRESH,
    SOURCE_NAMES,
    START_DATE,
    TVL_METRIC,
    TX_METRIC,
    client,
    pd,
    stringify,
):
    CHAIN_METRICS = {
        'DEFILLAMA_TVL': TVL_METRIC,
        'TXCOUNT': TX_METRIC,
        'FEES_PAID_ETH': FEES_METRIC,
        # 'STABLES_MCAP': 'Stablecoin Market Cap (USD)',
        # 'MARKET_CAP_USD': 'Market Cap (USD)',
        # 'MARKET_CAP_ETH': 'Market Cap (ETH)',
        # 'ACTIVE_DEPLOYERS': 'Active Deployers',
        # 'CONTRACTS_DEPLOYED': 'Contracts Deployed',
    }

    if REFRESH:    
        df_chain_metrics_raw = client.to_pandas(f"""
        SELECT
            sample_date,
            source,
            chain,
            metric_name,
            amount,
            SUM(amount / 30) OVER (
                PARTITION BY source, chain, metric_name
                ORDER BY sample_date
                RANGE BETWEEN INTERVAL '29' DAY PRECEDING AND CURRENT ROW
            ) AS rolling_30d_amount
        FROM int_chain_metrics
        WHERE
        chain IN ({stringify(CHAINS)})
        AND metric_name IN ({stringify(CHAIN_METRICS.keys())})
        AND sample_date BETWEEN DATE('{START_DATE}') AND DATE('{END_DATE}')
        """)
        df_chain_metrics_raw.to_csv("chain_metrics_raw.csv", index=False)
    else:
        df_chain_metrics_raw = pd.read_csv("chain_metrics_raw.csv")

    df_chain_metrics_raw['sample_date'] = pd.to_datetime(df_chain_metrics_raw['sample_date'])
    df_chain_metrics_raw['chain'] = df_chain_metrics_raw['chain'].apply(lambda x: x.title() if x.title() in SOURCE_NAMES else 'Others')
    df_chain_metrics_raw['metric'] = df_chain_metrics_raw['metric_name'].map(CHAIN_METRICS)
    df_chain_metrics_raw = df_chain_metrics_raw.groupby(['sample_date', 'source', 'chain', 'metric'])[['amount', 'rolling_30d_amount']].sum().reset_index()

    df_chain_metrics_raw
    return (df_chain_metrics_raw,)


@app.cell
def _(GC_MECHANISM_NAME, REFRESH, RF_MECHANISM_NAME, client, pd):
    if REFRESH:
        df_grants_raw = client.to_pandas(f"""
        SELECT
            DATE_TRUNC('MONTH', funding_date) AS funding_date,
            TRIM(BOTH '"' FROM json_extract_scalar(metadata,'$.application_name')) AS title,
            to_project_name,
            grant_pool_name,
            CAST(TRIM(BOTH '"' FROM json_extract_scalar(metadata,'$.token_amount')) AS DOUBLE) AS op_amount,
            amount AS usd_amount,
            TRIM(BOTH '"' FROM json_extract_scalar(metadata,'$.application_url')) AS url,
            CASE
                WHEN grant_pool_name LIKE '%season%' THEN CONCAT('Season ',substr(grant_pool_name,-1,1))
                WHEN grant_pool_name LIKE '%s7%' THEN 'Season 7'
                WHEN grant_pool_name='retropgf2' THEN 'Season 3'
                WHEN grant_pool_name='retropgf3' THEN 'Season 4'
                WHEN grant_pool_name='retrofunding4' THEN 'Season 5'
                WHEN grant_pool_name IN('retrofunding5','retrofunding6') THEN 'Season 6'
                ELSE 'Unknown'
            END AS season,
            CASE WHEN grant_pool_name LIKE '%retro%' THEN 'Retro Funding' ELSE 'Grants Council' END AS mechanism,
            CONCAT(
                CASE
                    WHEN grant_pool_name LIKE '%season%' THEN CONCAT('Season ',substr(grant_pool_name,-1,1))
                    WHEN grant_pool_name LIKE '%s7%' THEN 'Season 7'
                    WHEN grant_pool_name='retropgf2' THEN 'Season 3'
                    WHEN grant_pool_name='retropgf3' THEN 'Season 4'
                    WHEN grant_pool_name='retrofunding4' THEN 'Season 5'
                    WHEN grant_pool_name IN('retrofunding5','retrofunding6') THEN 'Season 6'
                    ELSE 'Unknown'
                END,
                ' - ',
                CASE WHEN grant_pool_name LIKE '%retro%' THEN '{RF_MECHANISM_NAME}' ELSE '{GC_MECHANISM_NAME}' END,
                ' - ',
                TRIM(BOTH '"' FROM json_extract_scalar(metadata,'$.application_name'))
            ) AS application
        FROM stg_ossd__current_funding
        WHERE
            from_funder_name='optimism'
            AND amount>0
        """)
        df_grants_raw.to_csv("grants_raw.csv", index=False)
    else:
        df_grants_raw = pd.read_csv("grants_raw.csv")

    df_grants_raw['funding_date'] = pd.to_datetime(df_grants_raw['funding_date'])
    df_grants_raw
    return (df_grants_raw,)


@app.cell
def _(
    CHAINS,
    END_DATE,
    REFRESH,
    SOURCE_NAMES,
    START_DATE,
    client,
    df_grants_raw,
    pd,
    stringify,
):
    OSO_PROJECT_NAMES = list(df_grants_raw['to_project_name'].dropna().unique())
    ONCHAIN_METRICS = {
        'defillama_tvl_daily': 'DefiLlama TVL (USD)',
        'gas_fees_daily': 'Fees Paid (ETH)',
        'transactions_daily': 'Transaction Count',
    #    'contract_invocations_daily': 'Contract Invocations Count',
    }
    CODE_METRICS = {
        'GITHUB_active_developers_monthly': 'Monthly Active Developers',
        'GITHUB_full_time_developers_monthly': 'Monthly Full-Time Developers',
    }
    ONCHAIN_METRIC_NAMES= [f"{c}_{m}" for c in CHAINS for m in ONCHAIN_METRICS.keys()]
    CODE_METRIC_NAMES = list(CODE_METRICS.keys())
    CODE_METRIC_LABELS = list(CODE_METRICS.values())

    METRICS = ONCHAIN_METRIC_NAMES + CODE_METRIC_NAMES

    if REFRESH:
        df_metrics_raw = client.to_pandas(f"""
        WITH metrics AS (
            SELECT DISTINCT
                sample_date,
                project_name,
                metric_name,
                amount,
                SUM(amount) OVER (
                    PARTITION BY project_name, metric_name
                    ORDER BY sample_date
                    RANGE BETWEEN INTERVAL '29' DAY PRECEDING AND CURRENT ROW
                ) AS rolling_30d_amount
            FROM timeseries_metrics_by_project_v0
            JOIN metrics_v0 USING (metric_id)
            JOIN projects_v1 USING (project_id)
            WHERE
                project_name IN ({stringify(OSO_PROJECT_NAMES)})
                AND metric_name IN ({stringify(METRICS)})
                AND sample_date BETWEEN DATE('{START_DATE}') AND DATE('{END_DATE}')
            ORDER BY sample_date, project_name, metric_name
        )
        SELECT
            sample_date,
            project_name,
            metric_name,
            amount,
            CASE
            WHEN metric_name LIKE '%daily' THEN rolling_30d_amount / 30
            ELSE amount
            END AS rolling_30d_amount
        FROM metrics
        """)
        df_metrics_raw.to_parquet("metrics_raw.parquet")
    else:
        df_metrics_raw = pd.read_parquet("metrics_raw.parquet")

    df_metrics_raw['chain'] = df_metrics_raw['metric_name'].apply(lambda x: x.split('_')[0])
    df_metrics_raw['chain'] = df_metrics_raw['chain'].apply(lambda x: x.title() if x.title() in SOURCE_NAMES else 'Others')

    df_metrics_raw['metric'] = df_metrics_raw['metric_name'].apply(lambda x: '_'.join(x.split('_')[1:]))
    df_metrics_raw['metric'] = df_metrics_raw['metric'].apply(lambda x: ONCHAIN_METRICS.get(x, CODE_METRICS.get(f'GITHUB_{x}')))
    df_metrics_raw['sample_date'] = pd.to_datetime(df_metrics_raw['sample_date'])
    df_metrics_raw.drop(columns=['metric_name'], inplace=True)

    df_metrics_raw = df_metrics_raw.groupby(['sample_date', 'project_name', 'chain', 'metric']).sum().reset_index()
    df_metrics_raw
    return CODE_METRIC_LABELS, df_metrics_raw


@app.cell
def _(END_DATE, RF_MECHANISM_NAME, START_DATE, df_grants_raw, pd):
    df_totals = df_grants_raw.groupby('mechanism', as_index=False).agg(
        total_usd=('usd_amount', 'sum'),
        total_op=('op_amount', 'sum'),
        applications=('application', 'nunique'),
        tracked_projects=('to_project_name', 'nunique')
    )
    df_totals['allocated_op'] = [231928234,841813590]

    df_coverage = df_grants_raw.pivot_table(
        index='mechanism', 
        columns=(df_grants_raw['to_project_name'] != ''), 
        values='op_amount', 
        aggfunc=('sum', 'nunique')
    )
    df_coverage.columns = [
        f"{agg.title()} {'(Mapped to OSO)' if proj else '(Unmapped)'}"
        if agg!='mechanism' else 'Mechanism'
        for agg, proj in df_coverage.columns.to_flat_index()
    ]
    df_coverage.reset_index(inplace=True)

    get_project_list = lambda lst: sorted(list(set([x for x in lst if isinstance(x, str) and x != ''])))
    df_seasons = (
        df_grants_raw
        .groupby(['mechanism','season'], as_index=False)
        .agg(
            start_date=('funding_date','min'),
            end_date=('funding_date','max'),
            total_usd=('usd_amount','sum'),
            total_op=('op_amount','sum'),
            count_all_projects=('application', 'nunique'),
            project_list=('to_project_name', get_project_list)
        )
        .sort_values('start_date')
        .assign(usd_to_op=lambda d: d['total_usd'] / d['total_op'])
    )
    df_seasons['count_oso_projects'] = df_seasons['project_list'].apply(len)

    is_retro = df_seasons['mechanism'] == RF_MECHANISM_NAME
    df_seasons['season_start_date'] = (df_seasons['start_date'] - pd.Timedelta(days=60)).where(is_retro, df_seasons['start_date']).clip(lower=START_DATE)
    df_seasons['season_end_date'] = df_seasons['end_date'].where(is_retro, df_seasons['end_date'] + pd.Timedelta(days=90)).clip(upper=END_DATE)
    df_seasons['analysis_start_date'] = (df_seasons['season_start_date'] - pd.Timedelta(days=90)).clip(lower=START_DATE)
    df_seasons['analysis_end_date'] = (df_seasons['season_end_date'] + pd.Timedelta(days=90)).clip(upper=END_DATE)

    df_seasons = (
        df_seasons
        .drop(columns=['start_date','end_date'])
        .assign(
            cumulative_op_by_mechanism=lambda d: d.groupby('mechanism')['total_op'].cumsum().round().astype(int),
            cumulative_usd_by_mechanism=lambda d: d.groupby('mechanism')['total_usd'].cumsum().round().astype(int)
        )
    )

    df_seasons
    return (df_seasons,)


@app.cell
def _(df_chain_metrics_raw, df_grants_raw, df_metrics_raw, df_seasons, np, pd):
    def materialize_checkpoints(wide_df, checkpoints):
        out = wide_df.copy()
        for label, ts in checkpoints.items():
            if ts in out.columns:
                out[label] = out[ts]
            else:
                out[label] = np.nan
        ts_cols = [c for c in out.columns if isinstance(c, pd.Timestamp)]
        if ts_cols:
            out = out.drop(columns=ts_cols)
        return out

    def generate_cohorts_and_comps():
        comps = []
        df_seasons_idx = df_seasons.set_index(['mechanism','season'])

        for (mechanism, season), grp in df_grants_raw.groupby(['mechanism','season']):
            projects = grp.to_project_name.dropna().unique()

            season_start = df_seasons_idx.at[(mechanism, season), 'season_start_date']
            season_end = df_seasons_idx.at[(mechanism, season), 'season_end_date']
            lookback = df_seasons_idx.at[(mechanism, season), 'analysis_start_date']
            lookahead = df_seasons_idx.at[(mechanism, season), 'analysis_end_date']

            checkpoints = {
                'Start Analysis': lookback,
                'Start Season': season_start,
                'End Season': season_end,
                'End Analysis': lookahead
            }
            dates = list(checkpoints.values())

            # Filter chain & project metrics for analysis window
            df_cm = df_chain_metrics_raw[
                df_chain_metrics_raw['sample_date'].between(lookback, lookahead, inclusive='both')
            ]
            df_m = df_metrics_raw[
                df_metrics_raw['project_name'].isin(projects) &
                df_metrics_raw['sample_date'].between(lookback, lookahead, inclusive='both')
            ]

            # Roll up per-project daily values
            df_grp = (
                df_m
                .groupby(['metric','project_name','sample_date'], as_index=False)['rolling_30d_amount']
                .sum()
            )

            # Project-level wide table (one row per metric×project)
            df_proj = (
                df_grp[df_grp['sample_date'].isin(dates)]
                .pivot_table(
                    index=['metric','project_name'],
                    columns='sample_date',
                    values='rolling_30d_amount',
                    fill_value=0
                )
                .pipe(materialize_checkpoints, checkpoints)
                .assign(cohort_type='Project')
                .reset_index()
            )

            # Aggregate across funded projects (metric×date summed)
            season_totals = (
                df_grp[df_grp['sample_date'].isin(dates)]
                .groupby(['metric','sample_date'])['rolling_30d_amount']
                .sum()
                .unstack()
                .pipe(materialize_checkpoints, checkpoints)
                .assign(project='Funded Projects', cohort_type='Aggregate')
                .reset_index()
            )

            # Aggregate entire superchain (metric×date summed)
            df_cg = (
                df_cm
                .groupby(['metric','sample_date'], as_index=False)['rolling_30d_amount']
                .sum()
            )
            superchain = (
                df_cg[df_cg['sample_date'].isin(dates)]
                .groupby(['metric','sample_date'])['rolling_30d_amount']
                .sum()
                .unstack()
                .pipe(materialize_checkpoints, checkpoints)
                .assign(project='Superchain (All Activity)', cohort_type='Aggregate')
                .reset_index()
            )

            # Combine and compute deltas / pct-change
            df_local = pd.concat(
                [df_proj.rename(columns={'project_name':'project'}), season_totals, superchain],
                sort=False,
                ignore_index=True
            )

            # Guard: ensure checkpoint columns exist
            required = ['Start Season','End Season']
            missing = [c for c in required if c not in df_local.columns]
            if missing:
                raise ValueError(
                    f"Missing expected checkpoint columns: {missing}. "
                    f"Check data coverage between {lookback} and {lookahead} for mechanism={mechanism}, season={season}"
                )

            df_local['Delta (End - Start Season)'] = df_local['End Season'] - df_local['Start Season']
            # Avoid divide-by-zero warnings; result will be inf/NaN which is handled later
            df_local['Percent Change'] = (df_local['End Season'] / df_local['Start Season']) - 1
            df_local['Mechanism'] = mechanism
            df_local['Season'] = season

            comps.append(df_local)

        df_all_metric_comps = pd.concat(comps, ignore_index=True)

        # Rename & reorder columns
        df_all_metric_comps.columns = [c.replace('_',' ').title() if isinstance(c, str) else c for c in df_all_metric_comps.columns]
        groupers = ['Project','Cohort Type','Season','Mechanism','Metric']
        others = [c for c in df_all_metric_comps.columns if c not in groupers]
        df_all_metric_comps = df_all_metric_comps[groupers + others]

        # Tagging logic
        def tag_sub(df_sub):
            delta = df_sub['Delta (End - Start Season)'].replace([np.inf, -np.inf], np.nan).dropna()
            pctchg = df_sub['Percent Change'].replace([np.inf, -np.inf], np.nan).dropna()
            if delta.empty or pctchg.empty:
                out = df_sub.copy()
                out['Performance Tag'] = '3 - Neutral'
                return out

            with np.errstate(invalid='ignore'):
                d80, d50, d20 = np.nanquantile(delta, [0.8, 0.5, 0.2])
                p80, p50, p20 = np.nanquantile(pctchg, [0.8, 0.5, 0.2])

            def f(r):
                if (
                    r['Start Analysis'] == 0 or
                    r['Start Season'] == 0 or
                    (r['End Season'] == 0 and r['End Analysis'] > 0)
                ):
                    return '0 - New Project / Missing Data'
                if r['Delta (End - Start Season)'] > d80 and r['Percent Change'] > p80:
                    return '5 - Top Performer'
                if r['Delta (End - Start Season)'] > d50 and r['Percent Change'] > p50:
                    return '4 - Outperform'
                if r['Delta (End - Start Season)'] < d20 and (r['Percent Change'] < p20 or r['Percent Change'] == -1.0):
                    return '1 - Poor Performer'
                if r['Delta (End - Start Season)'] < d50 and r['Percent Change'] < p50:
                    return '2 - Underperform'
                return '3 - Neutral'

            out = df_sub.copy()
            out['Performance Tag'] = out.apply(f, axis=1)
            return out

        mask = df_all_metric_comps['Cohort Type'] == 'Project'
        tagged = (
            df_all_metric_comps[mask]
            .groupby(['Season', 'Mechanism', 'Metric'], group_keys=False)
            .apply(tag_sub)
            .reset_index(drop=True)
        )
        others = df_all_metric_comps[~mask].copy()
        others['Performance Tag'] = '9 - Aggregate Benchmarks'

        df_all_metric_comps = pd.concat([tagged, others], ignore_index=True)
        return df_all_metric_comps

    df_results_by_cohort = generate_cohorts_and_comps()        
    df_results_by_cohort
    return


@app.cell
def _():
    LAYOUT_KWARGS = dict(
        hovermode='x unified',
        plot_bgcolor="white",
        paper_bgcolor="white",      
        margin=dict(l=40, r=40, t=60, b=40),
        #height=800,
    )
    TITLE_KWARGS = dict(
        x=0.015,
        xanchor='left',
        yanchor='bottom',
        pad=dict(t=10),
        font=dict(size=16)
    )
    VLINE_KWARGS = dict(
        line_dash="dash",
        line_color="black",
        line_width=1,
        annotation_position="top",
        row="all",
        col="all"
    )
    XAXIS_KWARGS = dict(
        showgrid=False,
        showticklabels=True,
        ticks="outside",
        title=""
    )
    YAXIS_KWARGS = dict(
        matches=None,
        showgrid=True,
        gridcolor="lightgray",
        gridwidth=1,
        showticklabels=True,
        nticks=5,
        title=""
    )

    def format_facet_title(ann, idx=0):
        metric = ann.text.split("=", 1)[1]
        ann.text      = f"<b>{metric}</b>"
        axis_id = "" if idx == 0 else str(idx+1)
        ann.xref      = f"x{axis_id} domain"
        ann.yref      = "y domain"
        ann.x         = 0
        ann.xanchor   = "left"
        ann.y         = 1
        ann.yanchor   = "bottom"
    return (
        LAYOUT_KWARGS,
        TITLE_KWARGS,
        VLINE_KWARGS,
        XAXIS_KWARGS,
        YAXIS_KWARGS,
        format_facet_title,
    )


@app.cell
def _(
    CODE_METRIC_LABELS,
    GC_MECHANISM_NAME,
    LAYOUT_KWARGS,
    RF_MECHANISM_NAME,
    SOURCE_NAMES,
    SOURCE_PALETTE,
    TITLE_KWARGS,
    VLINE_KWARGS,
    XAXIS_KWARGS,
    YAXIS_KWARGS,
    df_chain_metrics_raw,
    df_metrics_raw,
    df_seasons,
    format_facet_title,
    pd,
    px,
):
    def prep_timeseries_dataframes(season, mechanism):

        season_params = df_seasons[
            (df_seasons['season'] == season) & (df_seasons['mechanism'] == mechanism)
        ].iloc[0]
        cohort_names = [
            'Superchain (All Activity)',
            f"{season_params['season']} ({season_params['count_oso_projects']} Projects)"
        ]

        df_chain_metrics_filtered = df_chain_metrics_raw.groupby(['chain', 'metric', 'sample_date'], as_index=False)['rolling_30d_amount'].sum()
        df_chain_metrics_filtered['cohort'] = cohort_names[0]
        df_project_metrics_grouped_filtered = df_metrics_raw[
            (df_metrics_raw['project_name'].isin(season_params['project_list']))
        ].groupby(['chain', 'metric', 'sample_date'], as_index=False)['rolling_30d_amount'].sum()
        df_project_metrics_grouped_filtered['cohort'] = cohort_names[1]

        df = pd.concat([df_chain_metrics_filtered, df_project_metrics_grouped_filtered], axis=0)
        df = df.sort_values(by=['sample_date', 'metric', 'chain', 'cohort']).reset_index(drop=True)
        df = df[
            (df['sample_date'] >= season_params['analysis_start_date']) &
            (df['sample_date'] <= season_params['analysis_end_date'])
        ]

        return {
            "df": df,
            "season_params": season_params,
            "cohort_names": cohort_names
        }    


    def plot_metrics_by_season(timeseries_data, metric):
        df_season_timeseries = timeseries_data['df']
        fig = px.area(
            df_season_timeseries.query("metric == @metric"),
            x='sample_date',
            y='rolling_30d_amount',
            color='chain',
            color_discrete_map=SOURCE_PALETTE,
            facet_col='cohort',
            category_orders={'cohort': timeseries_data['cohort_names']},    
            facet_col_wrap=2,
            facet_col_spacing=0.05,
        )
        fig.for_each_trace(
            lambda trace: trace.update(
                legendrank=SOURCE_NAMES.index(trace.name) if trace.name in SOURCE_NAMES else len(SOURCE_NAMES)
                if trace.name in SOURCE_NAMES else len(SOURCE_NAMES)
            )
        )
        for idx, ann in enumerate(fig.layout.annotations):
            if ann.text.startswith("cohort="):
                format_facet_title(ann, idx)

        fig.add_vline(x=timeseries_data['season_params']['season_start_date'].timestamp() * 1000, annotation_text="Start", **VLINE_KWARGS)
        fig.add_vline(x=timeseries_data['season_params']['season_end_date'].timestamp() * 1000, annotation_text="End", **VLINE_KWARGS)
        fig.update_layout(
            title={"text": f"<b>{metric}</b>", **TITLE_KWARGS},
            legend=dict(traceorder="normal", title_text="Chain"), 
            **LAYOUT_KWARGS
        )

        fig.update_traces(hovertemplate="%{y:,.0f}")
        fig.update_xaxes(**XAXIS_KWARGS)
        fig.update_yaxes(**YAXIS_KWARGS)
        fig.show()        

    def plot_developer_metrics_by_season(timeseries_data):
        df_season_timeseries = timeseries_data['df']
        fig = px.area(
            df_season_timeseries.query("metric in @CODE_METRIC_LABELS"),
            x='sample_date',
            y='rolling_30d_amount',
            color='chain',
            color_discrete_map=SOURCE_PALETTE,
            facet_col='metric',
            category_orders={'metric': CODE_METRIC_LABELS},    
            facet_col_wrap=2,
            facet_col_spacing=0.05
        )
        fig.for_each_trace(
            lambda trace: trace.update(
                legendrank=SOURCE_NAMES.index(trace.name) if trace.name in SOURCE_NAMES else len(SOURCE_NAMES)
                if trace.name in SOURCE_NAMES else len(SOURCE_NAMES)
            )
        )
        for idx, ann in enumerate(fig.layout.annotations):
            if ann.text.startswith("metric="):
                format_facet_title(ann, idx)

        fig.add_vline(x=timeseries_data['season_params']['season_start_date'].timestamp() * 1000, annotation_text="Start", **VLINE_KWARGS)
        fig.add_vline(x=timeseries_data['season_params']['season_end_date'].timestamp() * 1000, annotation_text="End", **VLINE_KWARGS)
        fig.update_layout(
            title={"text": f"<b>Developer Activity</b>", **TITLE_KWARGS},
            legend=dict(traceorder="normal", title_text="Source"), 
            **LAYOUT_KWARGS
        )

        fig.update_traces(hovertemplate="%{y:,.0f}")
        fig.update_xaxes(**XAXIS_KWARGS)
        fig.update_yaxes(**YAXIS_KWARGS)
        fig.show()

    def plot_summary_metrics(metric):

        if metric not in CODE_METRIC_LABELS:
            dff = df_chain_metrics_raw.query("metric == @metric")
        else:
            dff = df_metrics_raw.query("metric == @metric").groupby(['chain', 'metric', 'sample_date'], as_index=False)['rolling_30d_amount'].sum()

        fig = px.area(
            dff,
            x='sample_date',
            y='rolling_30d_amount',
            color='chain',
            color_discrete_map=SOURCE_PALETTE
        )
        fig.for_each_trace(
            lambda trace: trace.update(
                legendrank=SOURCE_NAMES.index(trace.name) if trace.name in SOURCE_NAMES else len(SOURCE_NAMES)
                if trace.name in SOURCE_NAMES else len(SOURCE_NAMES)
            )
        )

        for _,row in df_seasons.iterrows():        
            if row['mechanism'] == GC_MECHANISM_NAME:
                text = f"S{row['season'][-1]}"
                fig.add_vline(
                    x=row['season_start_date'].timestamp() * 1000,
                    annotation_text=text,
                    line_color='black',
                    line_width=1,
                    line_dash="dash",
                    annotation_position="top"
                )
            if row['mechanism'] == RF_MECHANISM_NAME:
                fig.add_vline(
                    x=row['season_start_date'].timestamp() * 1000,
                    annotation_text='Retro<br>Funding',
                    line_color='#FF0420',
                    line_width=2,
                    annotation_position="top"
                )

        fig.update_layout(title={"text": f"<b>{metric}</b>", **TITLE_KWARGS}, **LAYOUT_KWARGS)
        fig.update_layout(legend=dict(x=0.01, y=1.0, xanchor='left', yanchor='top', title='', traceorder='normal'))

        fig.update_traces(hovertemplate="%{y:,.0f}")
        fig.update_xaxes(**XAXIS_KWARGS)
        fig.update_yaxes(**YAXIS_KWARGS)
    
        return fig
    return (plot_summary_metrics,)


@app.cell
def _(TX_METRIC, plot_summary_metrics):
    plot_summary_metrics(TX_METRIC)
    return


@app.cell
def _(FEES_METRIC, plot_summary_metrics):
    plot_summary_metrics(FEES_METRIC)
    return


@app.cell
def _(TVL_METRIC, plot_summary_metrics):
    plot_summary_metrics(TVL_METRIC)
    return


@app.cell
def _(plot_summary_metrics):
    plot_summary_metrics('Monthly Active Developers')
    return


@app.cell
def _(
    END_DATE,
    LAYOUT_KWARGS,
    START_DATE,
    TITLE_KWARGS,
    df_gas_by_chain,
    df_grants_raw,
    pd,
    px,
):
    def plot_revenue_vs_grants(df_gas_by_chain, df_grants_raw):

        df = (
            pd.concat({
                'Collective Revenue (ETH)*': df_gas_by_chain
                    .groupby('sample_date')['collective_revenue']
                    .sum()
                    .cumsum(),
                'Grants (OP)': df_grants_raw
                    .groupby('funding_date')['op_amount']
                    .sum()
                    .cumsum()
            }, axis=1)
            .fillna(method='ffill')
            .assign(**{'Grants (OP)': lambda d: d['Grants (OP)'].fillna(0)})
            .reset_index()
            .rename(columns={'index': 'Date'})
        )
        df = df[df['Date'].between(START_DATE, END_DATE)]
        fig = px.line(
            df,
            x='Date',
            y=['Collective Revenue (ETH)*', 'Grants (OP)'],
            labels={'value': 'Amount', 'variable': 'Metric'}
        )
        fig.update_traces(selector={'name': 'Grants (OP)'}, yaxis='y2', line=dict(width=5))
        fig.update_traces(selector={'name':'Collective Revenue (ETH)*'}, fill='tozeroy')
        fig.update_layout(
            title={"text": f"<b>Cumulative Revenue vs. Grants</b>", **TITLE_KWARGS},
            legend=dict(x=0.01, y=1.0, xanchor='left', yanchor='top', title=''),
            yaxis=dict(title='Collective Revenue (ETH)*', rangemode='tozero', showline=True, linecolor='black', linewidth=1),
            yaxis2=dict(title='Grants (OP)', overlaying='y', side='right', rangemode='tozero', showline=True, linecolor='black', linewidth=1),
            xaxis=dict(title='', showline=True, linecolor='black', linewidth=1, ticks='outside'),
            **LAYOUT_KWARGS
        )
        fig.update_yaxes(showgrid=False, ticks='outside')
        fig.update_traces(hovertemplate="%{y:,.0f}")
        fig.show()

    plot_revenue_vs_grants(df_gas_by_chain, df_grants_raw)
    return


if __name__ == "__main__":
    app.run()
