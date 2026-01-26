import marimo

__generated_with = "unknown"
app = marimo.App()


@app.cell
def _(mo):
    mo.md(
        """
    # Measuring Chainlink's impact on OP Mainnet
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">Optimism</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2025-11-11</span></small>
    """
    )
    return


@app.cell
def _(
    defi_apps_headline,
    df_artifacts,
    indirect_revenue_headline,
    market_share_headline,
    mo,
    overall_takeaway,
    revenue_headline,
):
    _context = f"""
    - Chainlink has a total of [{len(df_artifacts[df_artifacts['project_name'] == 'chainlink'])} contracts](https://docs.google.com/spreadsheets/d/1V2kQTufvd9Hx5IIORM6tCTarKJ0KtogD1DDCgboZIa0/edit?usp=sharing) on OP Mainnet, most of which are oracle contracts used by defi applications.
    - The main alternative oracle to Chainlink on OP Mainnet is [Pyth](https://docs.pyth.network/price-feeds/contract-addresses/evm).
    - Oracle contracts are not invoked directly; they are typically invoked as read operations within a defi transaction.
    - This analysis looks at the direct and indirect impact of these oracle contracts in terms of revenue to OP Mainnet
    """

    _insights = f"""
    1. {market_share_headline}.
    2. {revenue_headline}.
    3. {defi_apps_headline}.
    4. {indirect_revenue_headline}.
    5. {overall_takeaway}.
    """

    mo.accordion({
        "Context": _context,
        "Key Insights": _insights,
        "Data Sources": """
        - [Superchain Data (c/o Goldsky)](https://bit.ly/superchain-public-data) - Source of raw transaction and traces data
        - [DefiLlama](https://defillama.com/) - Source of raw TVL data
        - [Chainlink DevHub](https://docs.chain.link/data-feeds/using-data-feeds) - Oracle addresses on OP Mainnet    
        - [OSS Directory](https://github.com/opensource-observer/oss-directory) - OSO's public project and address registry
        - [OSO API](https://docs.opensource.observer/docs/get-started/python) - Data and metrics pipeline
        """
    })    
    return


@app.cell
def _(PLOTLY_LAYOUT, df_chainlink_market_share, mo, pd, px):
    _df = df_chainlink_market_share.copy()
    _df['bucket_day'] = pd.to_datetime(_df['bucket_day'])

    _chainlink_market_share = _df['chainlink_share'].mean()
    _n = _df['total_transactions'].sum()
    market_share_headline = f"Chainlink has averaged {_chainlink_market_share:,.1f}% market share (vs Pyth) since the launch of OP Mainnet"

    _fig = px.area(data_frame=_df, x='bucket_day', y='chainlink_share')
    _fig.update_layout(**PLOTLY_LAYOUT)
    mo.vstack([
        mo.md(f"""
        ### **{market_share_headline}**
        n = {_n:,.0f} transactions with a read operation to an oracle contract on OP Mainnet
        """),
        mo.ui.plotly(_fig)
    ])
    return (market_share_headline,)


@app.cell
def _(
    END_YEAR,
    PLOTLY_LAYOUT,
    START_YEAR,
    df_chainlink_readops_rev,
    df_op_mainnet_rev,
    mo,
    pd,
    px,
):
    op_mainnet__all_time_rev  = df_op_mainnet_rev['amount'].sum()
    op_mainnet__past_year_rev = df_op_mainnet_rev[df_op_mainnet_rev['sample_date'].between(START_YEAR, END_YEAR)]['amount'].sum()

    _df = df_chainlink_readops_rev.copy()

    chainlink__all_time_rev  = _df['direct_revenue'].sum()
    chainlink__past_year_rev = _df[_df['bucket_day'].between(START_YEAR, END_YEAR)]['direct_revenue'].sum()

    _df['bucket_day'] = pd.to_datetime(_df['bucket_day'])
    _df['cumulative_revenue'] = _df['direct_revenue'].cumsum()

    revenue_headline = f"Chainlink directly contributed ~{chainlink__past_year_rev:,.0f} ETH in revenue to OP Mainnet over the past year ({chainlink__all_time_rev:,.0f} ETH all time)"

    fig_direct_revenue = px.area(data_frame=_df, x='bucket_day', y='cumulative_revenue',)
    fig_direct_revenue.update_layout(**PLOTLY_LAYOUT)
    mo.vstack([
        mo.md(f"""
        ---
        ### **{revenue_headline}**
        This estimate is based on the L2 gas fees associated with read operations only. This is {chainlink__past_year_rev / op_mainnet__past_year_rev * 100:,.1f}% of total revenue on OP Mainnet over the past year.
        """),
        mo.ui.plotly(fig_direct_revenue)
    ])
    return (
        chainlink__all_time_rev,
        chainlink__past_year_rev,
        op_mainnet__all_time_rev,
        op_mainnet__past_year_rev,
        revenue_headline,
    )


@app.cell
def _(df_oracle_usage_by_application, mo):
    list_of_defi_apps = list(df_oracle_usage_by_application[
        (df_oracle_usage_by_application['Chainlink Share of Oracle Txns'] >= 90) 
        & (df_oracle_usage_by_application['TVL (USD)'] >= 1_000_000)
    ]['oso_slug'].unique())

    _df = df_oracle_usage_by_application[df_oracle_usage_by_application['oso_slug'].isin(list_of_defi_apps)].copy()
    defi_app_names = _df.set_index('oso_slug')['Application'].drop_duplicates().dropna().to_dict()

    _df = _df.sort_values(by='TVL (USD)', ascending=False)
    top10_defi_apps = list(_df.head(10)['oso_slug'])

    _cols = ['Application', 'TVL (USD)', 'Total L2 Fees (ETH)', '# Chainlink Txns', 'Chainlink Share of Oracle Txns']
    _df = _df[_cols]

    defi_apps__past_year_rev = _df['Total L2 Fees (ETH)'].sum()
    defi_apps__current_tvl   = _df['TVL (USD)'].sum() / 1_000_000

    defi_apps_headline = f"DeFi apps using Chainlink contributed ~{defi_apps__past_year_rev:,.0f} ETH in revenue and a total of ~${defi_apps__current_tvl:,.0f}M TVL to OP Mainnet"

    mo.vstack([
        mo.md(f"""
        ---
        ### **{defi_apps_headline}**
        This estimate is based on the total L2 fees and average TVL for each app, from Oct 2024 to Sep 2025. Our assumption is that Chainlink is foundational infrastructure for these applications, even if they don't read from the price feed in each transaction. For example, both Uniswap and Velodrome appear to use Chainlink rather than Pyth as their price oracle, but don't call it as frequently as other defi apps.

        Note: apps with TVL below $1M and/or less than 90% Chainlink Share are filtered out of this analysis.
        """),
        mo.ui.table(
            data=_df.reset_index(drop=True),
            show_column_summaries=False,
            show_data_types=False,
            format_mapping={'Chainlink Share of Oracle Txns': '{:.1f}%', 'TVL (USD)': '${:,.0f}', '# Chainlink Txns': '{:,.0f}'},
            page_size=10
        )
    ])
    return (
        defi_app_names,
        defi_apps__past_year_rev,
        defi_apps_headline,
        top10_defi_apps,
    )


@app.cell
def _(PLOTLY_LAYOUT, defi_app_names, df_app_fees, mo, px, top10_defi_apps):
    defi_apps__all_time_rev = df_app_fees[df_app_fees['project_name'].isin(defi_app_names)]['revenue'].sum()

    _df = (
        df_app_fees[df_app_fees['project_name'].isin(top10_defi_apps)]
        .groupby(['sample_date', 'project_name'], as_index=False)['revenue']
        .sum()
        .sort_values('sample_date')
    )
    _df['Defi App'] = _df['project_name'].map(defi_app_names)
    _df['30D Rolling Revenue (ETH)'] = (
        _df
        .groupby('Defi App')['revenue']
        .transform(lambda x: x.rolling(window=30, min_periods=1).mean())
    )

    _fig = px.area(data_frame=_df, x='sample_date', y='30D Rolling Revenue (ETH)', color='Defi App')
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(hovermode='x unified', xaxis=dict(hoverformat='<b>%d %b %Y</b>'))
    _fig.update_traces(hovertemplate='%{fullData.name}: %{y:.4f} ETH<extra></extra>', hoverlabel=dict(namelength=-1))

    mo.vstack([
        mo.md(f"""
        ---
        ### **Perps platforms (eg, Synthetix) and DEXs (eg, Uniswap, Velodrome) have historically been the heaviest users of oracle data**
        This chart analyzes the revenue (30D trailing average) earned from the top 10 DeFi apps (by TVL) on OP Mainnet. All appear to use Chainlink as their primary oracle.
        """),
        mo.ui.plotly(_fig)
    ])
    return (defi_apps__all_time_rev,)


@app.cell
def _(END_YEAR, PLOTLY_LAYOUT, START_YEAR, df_top_level_app_fees, mo, px):
    _df = df_top_level_app_fees[df_top_level_app_fees['bucket_day'].between(START_YEAR, END_YEAR)]
    defi_apps_top_level__past_year_rev = _df[_df['app_type'] == 'defi']['revenue'].sum()
    unknown_top_level__past_year_rev   = _df[_df['app_type'] == 'unknown']['revenue'].sum()

    _df = df_top_level_app_fees.copy()
    defi_apps_top_level__all_time_rev  = _df[_df['app_type'] == 'defi']['revenue'].sum()
    unknown_top_level__all_time_rev    = _df[_df['app_type'] == 'unknown']['revenue'].sum()

    _df['Rolling Revenue (ETH)'] = _df.groupby('app_type')['revenue'].transform(lambda x: x.rolling(window=30, min_periods=1).mean())

    _fig = px.area(data_frame=_df[_df['app_type'] == 'unknown'], x='bucket_day', y='Rolling Revenue (ETH)')
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(hovermode='x unified', xaxis=dict(hoverformat='<b>%d %b %Y</b>'), showlegend=False)
    _fig.update_traces(hovertemplate='%{fullData.name}: %{y:.4f} ETH<extra></extra>', hoverlabel=dict(namelength=-1))

    _defi_share = defi_apps_top_level__all_time_rev / (unknown_top_level__all_time_rev + defi_apps_top_level__all_time_rev) * 100

    indirect_revenue_headline = f"Trading / arbitrage bots that call Chainlink oracles may contribute a further ~{unknown_top_level__past_year_rev:,.0f} ETH/year in revenue on OP Mainnet (~{unknown_top_level__all_time_rev:,.0f} ETH all time)"

    mo.vstack([
        mo.md(f"""
        ---

        ### **{indirect_revenue_headline}**

        This analysis looks at the total L2 fees associated with top-level transactions that include a Chainlink read operation in their trace data. A large share ({_defi_share:,.0f}%) of Chainlink's transactions can be linked to defi applications. Many of the "unknown" addresses appear to be arbitrage bots.
        """),
        mo.ui.plotly(_fig)
    ])
    return (
        indirect_revenue_headline,
        unknown_top_level__all_time_rev,
        unknown_top_level__past_year_rev,
    )


@app.cell
def _(
    chainlink__all_time_rev,
    chainlink__past_year_rev,
    defi_apps__all_time_rev,
    defi_apps__past_year_rev,
    mo,
    op_mainnet__all_time_rev,
    op_mainnet__past_year_rev,
    unknown_top_level__all_time_rev,
    unknown_top_level__past_year_rev,
):
    _lower_range__past_year = chainlink__past_year_rev
    _lower_range__all_time  = chainlink__all_time_rev

    _upper_range__past_year = unknown_top_level__past_year_rev + defi_apps__past_year_rev
    _upper_range__all_time  = unknown_top_level__all_time_rev  + defi_apps__all_time_rev

    overall_takeaway = f"Overall, Chainlink's revenue impact is in the range of {_lower_range__past_year:,.0f} to {_upper_range__past_year:,.0f} ETH, out of a total {op_mainnet__past_year_rev:,.0f} ETH of revenue earned on OP Mainnet in the past year"

    _md_table = mo.md(
    f"""

    | Source                                             | Revenue - Past Year                         | Revenue - All Time                         |
    |:---------------------------------------------------|--------------------------------------------:|-------------------------------------------:|
    | Chainlink - Direct revenue from read operations    | {chainlink__past_year_rev:,.1f} ETH         | {chainlink__all_time_rev:,.0f} ETH         |
    | DeFi Apps - All revenue from transactions          | {defi_apps__past_year_rev:,.0f} ETH         | {defi_apps__all_time_rev:,.0f} ETH         |
    | Trading / Arb bots - All revenue from transactions | {unknown_top_level__past_year_rev:,.0f} ETH | {unknown_top_level__all_time_rev:,.0f} ETH |
    | OP Mainnnet - All revenue from all sources         | {op_mainnet__past_year_rev:,.0f} ETH        | {op_mainnet__all_time_rev:,.0f} ETH        |
    | _Lower Bound Estimate (Chainlink only)_            | _{_lower_range__past_year:,.1f} ETH_        | _{_lower_range__all_time:,.0f} ETH_        |
    | _Upper Bound Estimate (DeFi + Trading/Arb bots)_   | _{_upper_range__past_year:,.0f} ETH_        | _{_upper_range__all_time:,.0f} ETH_        |

    """)


    mo.vstack([
        mo.md(f"""
        ---
        ### **{overall_takeaway}**
        The table below summarizes the methodology used to construct a lower and upper bound estimate. The lower bound only considers the direct impact of Chainlink read operations, whereas the upper bound considers all revenue from DeFi apps and trading / arb bots that use Chainlink in some way.
        """),
        _md_table
    ])
    return (overall_takeaway,)


@app.cell
def _():
    # Queries
    return


@app.cell
def _(mo, pyoso_db_conn):
    df_chainlink_market_share = mo.sql(
        f"""
        WITH tx AS (
          SELECT
            bucket_day,
            SUM(CASE WHEN oracle_name = 'chainlink' THEN CAST(transaction_count AS DOUBLE) ELSE 0 END) AS chainlink,
            SUM(CAST(transaction_count AS DOUBLE)) AS total_transactions
          FROM int_optimism_oracles_direct_fees_daily
          GROUP BY 1
        )
        SELECT
          bucket_day,
          ROUND(chainlink/total_transactions*100,2) AS chainlink_share,
          chainlink AS chainlink_transactions,
          total_transactions
        FROM tx
        ORDER BY 1
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_chainlink_market_share,)


@app.cell
def _(mo, pyoso_db_conn):
    df_op_mainnet_rev = mo.sql(
        f"""
        SELECT
          sample_date,
          amount
        FROM int_chain_metrics
        WHERE chain = 'OPTIMISM'
        AND metric_name = 'LAYER2_GAS_FEES'
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_op_mainnet_rev,)


@app.cell
def _(mo, pyoso_db_conn):
    df_chainlink_readops_rev = mo.sql(
        f"""
        SELECT
          bucket_day,
          SUM(read_fees) AS direct_revenue
        FROM int_optimism_oracles_direct_fees_daily
        WHERE oracle_name = 'chainlink'
        GROUP BY 1
        ORDER BY 1
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_chainlink_readops_rev,)


@app.cell
def _(END_YEAR, START_YEAR, mo, pyoso_db_conn):
    df_oracle_usage_by_application = mo.sql(
        f"""
        WITH base AS (
          SELECT
            to_project_name AS application,
            oracle_name,
            CAST(tx_count AS INT) AS tx_count
          FROM int_optimism_oracles_indirect_fees_daily
          WHERE bucket_day BETWEEN DATE('{START_YEAR}') AND DATE('{END_YEAR}')
        ),
        agg AS (
          SELECT
            application,
            SUM(tx_count) AS total_tx,
            SUM(CASE WHEN oracle_name = 'chainlink' THEN tx_count ELSE 0 END) AS chainlink_tx
          FROM base
          GROUP BY application
        ),
        with_share AS (
          SELECT
            application,
            chainlink_tx,
            total_tx,
            CAST(chainlink_tx AS DOUBLE)/NULLIF(total_tx,0) AS chainlink_share
          FROM agg
        ),
        app_raw_metrics AS (
          SELECT
            with_share.application,
            tm.sample_date,
            MAX(CASE WHEN m.metric_model = 'defillama_tvl' THEN tm.amount ELSE 0 END) AS defillama_tvl,
            MAX(CASE WHEN m.metric_model = 'layer2_gas_fees' THEN tm.amount / 1e18 ELSE 0 END) AS revenue
          FROM timeseries_metrics_by_project_v0 tm
          JOIN metrics_v0 m USING metric_id
          JOIN projects_v1 p USING project_id
          JOIN with_share ON p.project_name = with_share.application
          WHERE
            tm.sample_date BETWEEN DATE('{START_YEAR}') AND DATE('{END_YEAR}')
            AND m.metric_model IN ('layer2_gas_fees', 'defillama_tvl')
            AND m.metric_time_aggregation = 'daily'  
            AND m.metric_event_source = 'OPTIMISM'
            AND p.project_source = 'OSS_DIRECTORY'
            AND p.project_namespace = 'oso'
          GROUP BY 1,2
        ),
        app_metrics AS (
          SELECT
            application,
            AVG(defillama_tvl) AS defillama_tvl,
            SUM(revenue) AS revenue
          FROM app_raw_metrics
          GROUP BY 1
        )
        SELECT
          application AS oso_slug,
          p.display_name AS "Application",
          chainlink_tx AS "# Chainlink Txns",
          ROUND(total_tx,0) AS "Total Oracle Txns",
          ROUND(chainlink_share*100,2) AS "Chainlink Share of Oracle Txns",
          ROUND(defillama_tvl,0) AS "TVL (USD)",
          ROUND(revenue,2) AS "Total L2 Fees (ETH)"
        FROM with_share
        JOIN app_metrics USING application
        JOIN projects_v1 p
          ON application = p.project_name
          AND project_source = 'OSS_DIRECTORY'
          AND project_namespace = 'oso'
        ORDER BY 7 DESC
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_oracle_usage_by_application,)


@app.cell
def _(mo, pyoso_db_conn):
    df_app_fees = mo.sql(
        f"""
        SELECT
          sample_date,
          project_name,
          amount / 1e18 AS revenue
        FROM timeseries_metrics_by_project_v0
        JOIN metrics_v0 USING metric_id
        JOIN projects_v1 USING project_id
        WHERE
          metric_model = 'layer2_gas_fees'
          AND metric_time_aggregation = 'daily'  
          AND metric_event_source = 'OPTIMISM'
          AND project_source = 'OSS_DIRECTORY'
          AND project_namespace = 'oso'
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_app_fees,)


@app.cell
def _(mo, pyoso_db_conn):
    df_top_level_app_fees = mo.sql(
        f"""
        SELECT
          bucket_day,
          CASE WHEN to_project_name IS NULL THEN 'unknown' ELSE 'defi' END AS app_type,
          SUM(CAST(l2_tx_fees AS DOUBLE)) AS revenue
        FROM int_optimism_oracles_indirect_fees_daily
        WHERE oracle_name = 'chainlink'
        GROUP BY 1,2
        ORDER BY 1,2
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_top_level_app_fees,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ---

    # Methodology Details

    ## Direct Revenue 

    ### ✅ Part 1. Contract labeling

    We created a comprehensive list of all oracle contract addresses (e.g., CCIP, price feeds, aggregators).

    All relevant [Chainlink](https://docs.chain.link/data-feeds/using-data-feeds) and [Pyth Network](https://docs.pyth.network/price-feeds/contract-addresses/evm) contracts deployed on OP Mainnet as 2025-10-01 are available in the `int_optimism_oracle_addresses` model and as an export [here](https://docs.google.com/spreadsheets/d/1V2kQTufvd9Hx5IIORM6tCTarKJ0KtogD1DDCgboZIa0/edit?usp=sharing).
    """
    )
    return


@app.cell
def _(mo, pyoso_db_conn):
    df_artifacts = mo.sql(
        f"""
        SELECT * FROM int_optimism_oracle_addresses
        """,
        engine=pyoso_db_conn
    )
    return (df_artifacts,)


@app.cell
def _(df_artifacts):
    addresses = list(df_artifacts['artifact_name'].unique())
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ### ✅ Part 2. Calculate fees associated with read operations from trace data

    We built a separate table to read operations (from traces) and joined the traces on transaction data. The formula used for direct revenue of oracle contracts is:

    \[
    \texttt{GAS\_READ\_OPERATION} = 
    \frac{\texttt{gas\_used\_trace} \times \texttt{gas\_price\_tx}}{10^{18}}
    \]

    Here are some sample transactions to sanity check:
    """
    )
    return


@app.cell
def _(mo):
    address_select = mo.ui.text(
        label='Address:',
        value='0x13e3ee699d1909e989722e753853ae30b17e08c5',
        full_width=True
    )
    date_range = mo.ui.date_range(
        start='2025-09-01',
        stop='2025-09-02',
        full_width=True,
        label='Date range to sample:'
    )
    mo.vstack([
        address_select,
        date_range
    ])
    return address_select, date_range


@app.cell
def _(address_select, date_range, mo, pyoso_db_conn):
    df_net_fees = mo.sql(
        f"""
        SELECT
          gas_used_trace,
          gas_price_tx,
          gas_used_tx,    
          gas_used_trace * gas_price_tx  / 1e9 AS "GAS_READ_OPERATION (WEI)",
          gas_used_tx * gas_price_tx / 1e9 AS "L2_FEES (WEI)",
          l1_fee,
          txs_in_block,
          trace_address,
          'https://optimistic.etherscan.io/tx/' || transaction_hash AS transaction_hash
        FROM int_optimism_static_calls_to_oracles
        WHERE
          block_timestamp BETWEEN DATE('{date_range.value[0]}') AND DATE('{date_range.value[1]}')
          AND to_address_trace = '{address_select.value}'
        LIMIT 10
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Indirect Revenue

    ### ✅ Part 1. Analyze which protocols use Chainlink

    We look up all addresses that appear in read operations and see if we can identify the application that is calling it. We will assume that the `to_address` in the top level transaction is the application and `to_address` in the read operation is the oracle. If we wanted to go further, we could add special handling for userops, which currently show up bundled in 4337 and multi-sig transactions.

    Here are some sample transactions (linked to Aave) to sanity check:
    """
    )
    return


@app.cell
def _(date_range, mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        WITH apps AS (
            SELECT DISTINCT
              artifact_name,
              project_name
            FROM artifacts_by_project_v1
            WHERE
              project_source = 'OSS_DIRECTORY'
              AND artifact_source = 'OPTIMISM'
              AND project_name = 'aave'
        )

        SELECT
          sc.project_name AS oracle,
          apps.project_name AS application,
          gas_used_trace,
          gas_price_tx,
          gas_used_tx,
          gas_used_trace * gas_price_tx  / 1e9 AS "GAS_READ_OPERATION (WEI)",    
          gas_used_tx * gas_price_tx / 1e9 AS "L2_FEES (WEI)",
          'https://optimistic.etherscan.io/tx/' || transaction_hash AS transaction_hash  
        FROM int_optimism_static_calls_to_oracles AS sc
        JOIN apps
          ON sc.to_address_tx = apps.artifact_name
        WHERE
          sc.block_timestamp BETWEEN DATE('{date_range.value[0]}') AND DATE('{date_range.value[1]}')
        LIMIT 10
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    Arbitrage / MEV / trading bots are also heavy users of oracles.

    Here are some high-volume users of price oracles that are not linked to any known applications:
    """
    )
    return


@app.cell
def _(date_range, mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          bucket_day AS date,
          oracle_name,
          'https://optimistic.etherscan.io/address/' || to_address AS to_address,
          tx_count AS num_transactions
        FROM int_optimism_oracles_indirect_fees_daily
        WHERE
          bucket_day BETWEEN DATE('{date_range.value[0]}') AND DATE('{date_range.value[1]}')
          AND to_project_name IS NULL
        ORDER BY tx_count DESC
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    It's worth noting that some major defi apps (eg, Velodrome, Uniswap) have relatively little oracle activity, which suggests they may be accessing price feed data some other way. 

    Here's a sample of Velodrome's read operations from the data range selected above:
    """
    )
    return


@app.cell
def _(date_range, mo, pyoso_db_conn):
    df_velo = mo.sql(
        f"""
        WITH velo AS (
          SELECT DISTINCT artifact_name AS address
          FROM artifacts_by_project_v1
          WHERE
            project_source = 'OSS_DIRECTORY'
            AND artifact_source = 'OPTIMISM'
            AND project_name = 'velodrome'
        ),
        events AS (
          SELECT
            tx.transaction_hash,
            tx.to_address_trace AS read_to_address
          FROM int_superchain_static_calls_txs_joined AS tx
          JOIN velo
            ON tx.to_address_tx = velo.address
          WHERE
            tx.block_timestamp BETWEEN DATE('{date_range.value[0]}') AND DATE('{date_range.value[1]}')
        )

        SELECT
          'https://optimistic.etherscan.io/address/' || events.read_to_address AS "Address in Read Operations",
          COALESCE(abp.project_name, 'unknown') AS "Address Owner",
          COUNT(DISTINCT events.transaction_hash) AS "Num Txns Invoking This Address"
        FROM events
        LEFT JOIN artifacts_by_project_v1 AS abp
          ON
            events.read_to_address = abp.artifact_name
            AND abp.project_source = 'OSS_DIRECTORY'    
            AND abp.artifact_source = 'OPTIMISM'        
        GROUP BY 1,2
        ORDER BY 3 DESC
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ### ✅ Part 2. Estimate the value of the defi ecosystem downstream from Chainlink oracles

    This analysis gets sets an upper bound estimate of Chainlink's impact on OP Mainnet. We identify defi apps (defined as apps with at least $1M in TVL on OP Mainnet) and calculate their total L2 fees.

    Note: this is different than the analysis in Part 1, where we only looked at the top-level L2 fees in transactions that invoke an oracle. Here, we look at ALL L2 fees generated by apps that use Chainlink. The rationale is that Chainlink is critical infrastructure for these defi apps regardless of whether they utilize it directly in each transaction or indirectly in some other way.
    """
    )
    return


@app.cell
def _(date_range, mo, pyoso_db_conn):
    df_app_preview = mo.sql(
        f"""
        WITH with_share AS (
          SELECT
            to_project_name AS application,
            oracle_name,
            SUM(CAST(tx_count AS INT)) AS tx_count
          FROM int_optimism_oracles_indirect_fees_daily
          WHERE bucket_day BETWEEN DATE('{date_range.value[0]}') AND DATE('{date_range.value[1]}')
          GROUP BY 1,2
        ),
        metrics AS (
        SELECT
          tm.sample_date AS "Sample Date",    
          with_share.application AS "Application",
          with_share.oracle_name AS "Oracle",
          with_share.tx_count AS "Num Txns Invoking This Oracle", 
          MAX(CASE WHEN m.metric_model = 'defillama_tvl' THEN tm.amount ELSE 0 END) AS "App TVL (USD)",
          MAX(CASE WHEN m.metric_model = 'layer2_gas_fees' THEN tm.amount / 1e18 ELSE 0 END) AS "App L2 Fees (ETH)"
        FROM timeseries_metrics_by_project_v0 tm
        JOIN metrics_v0 m USING metric_id
        JOIN projects_v1 p USING project_id
        JOIN with_share
          ON p.project_name = with_share.application
        WHERE
          tm.sample_date BETWEEN DATE('{date_range.value[0]}') AND DATE('{date_range.value[1]}')
          AND m.metric_model IN ('layer2_gas_fees', 'defillama_tvl')
          AND m.metric_time_aggregation = 'daily'  
          AND m.metric_event_source = 'OPTIMISM'
        GROUP BY 1,2,3,4
        )
        SELECT DISTINCT * FROM metrics
        ORDER BY 1,2
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell
def _(mo):
    mo.md(r"""#### Other metrics about these apps (if we want them)""")
    return


@app.cell
def _(date_range, mo, pyoso_db_conn):
    df_all_metrics = mo.sql(
        f"""
        SELECT
          project_name,
          metric_model,
          AVG(amount) AS avg_amount
        FROM timeseries_metrics_by_project_v0
        JOIN metrics_v0 USING metric_id
        JOIN projects_v1 USING project_id
        WHERE
          project_name = 'aave'
          AND sample_date BETWEEN DATE('{date_range.value[0]}') AND DATE('{date_range.value[1]}')
          AND metric_event_source = 'OPTIMISM'
          AND metric_time_aggregation = 'daily'
        GROUP BY 1,2
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell
def _():
    # Helpers / Imports
    #
    # only visible in code view 
    return


@app.cell
def _():
    PLOTLY_LAYOUT = dict(
        title="",
        barmode="relative",
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=12, color="#111"),
        margin=dict(t=0, l=0, r=0, b=50),
        legend=dict(
            orientation="v",
            yanchor="top", y=0.98,
            xanchor="left", x=0.02,
            bordercolor="black", borderwidth=1,
            bgcolor="white"
        ),
        xaxis=dict(
            title="",
            showgrid=False,
            linecolor="#000", linewidth=1,
            ticks="outside", tickformat="%b %Y"
        ),
        yaxis=dict(
            title="",
            showgrid=True, gridcolor="#DDD",
            zeroline=True, zerolinecolor="black", zerolinewidth=1,
            linecolor="#000", linewidth=1,
            ticks="outside", range=[0, None]
        )
    )
    return (PLOTLY_LAYOUT,)


@app.cell
def _():
    START_YEAR = '2024-10-01'
    END_YEAR = '2025-09-30'
    return END_YEAR, START_YEAR


@app.cell
def _():
    stringify = lambda arr: "'" + "','".join(arr) + "'"
    return


@app.cell
def _():
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
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
