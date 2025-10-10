import marimo

__generated_with = "0.16.2"
app = marimo.App(width="full")


@app.cell
def _():
    import numpy as np
    import pandas as pd
    import matplotlib
    import matplotlib.pyplot as plt
    import seaborn as sns
    return matplotlib, np, pd, plt, sns


@app.cell
def _(matplotlib):
    # styling constants
    matplotlib.rcParams.update({'font.family': 'monospace'})

    # some styling constants
    PURPLE = '#6935FF'
    GREEN = '#3A4934'
    WHITE = '#FAF7F3'
    SMALL = 10

    # date constants
    START = '2018Q1'
    END = '2023Q4'
    return END, GREEN, PURPLE, SMALL, START, WHITE


@app.cell
def _():
    DATA_URL_BASE = "https://raw.githubusercontent.com/opensource-observer/insights/refs/heads/main/analysis/gitcoin/data"
    return (DATA_URL_BASE,)


@app.cell
def _(DATA_URL_BASE, pd):
    project_names = pd.read_json(f"{DATA_URL_BASE}/gitcoin-project-names.json").set_index('slug')['name'].to_dict()
    return (project_names,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Overall grants analysis""")
    return


@app.cell
def _(DATA_URL_BASE, pd):
    g = pd.read_csv(f"{DATA_URL_BASE}/csv/gitcoin_allo%2Bcgrants_all.csv", index_col=0)

    # load and arrange the funding round data
    g['quarter'] = pd.PeriodIndex(g.round_date, freq='Q')
    g['quarter'] = g['quarter'].apply(str)

    def name_round(rid, rname):
        if '0x' in rid:
            return rname
        else:
            return f"GR{rid}"
    g['round'] = g.apply(lambda x: name_round(x['round_id'], x['round_name']), axis=1)

    # manual updates to clean a few rounds that are on the edge of a quarter
    g.loc[g['round'] == 'GR2', 'quarter'] = '2019Q2'
    g.loc[g['round'] == 'GR4', 'quarter'] = '2019Q4'

    # rename allo grants
    g.loc[g['quarter'] == '2023Q1', 'round'] = 'Alpha'
    g.loc[g['quarter'] == '2023Q2', 'round'] = 'Beta'
    g.loc[g['quarter'] == '2023Q3', 'round'] = 'GG18'
    g.loc[g['quarter'] == '2023Q4', 'round'] = 'GG19'

    g.head(1)
    return (g,)


@app.cell
def _(g):
    print("Total ($M):", g['total_usd'].sum() / 1_000_000)
    print("Matching pools ($M):", g['match_usd'].sum() / 1_000_000)
    multiplier = g['total_usd'].sum()/g['match_usd'].sum()
    print("Multiplier:", multiplier)
    print("Applications:", len(g))
    print("Est projects:", len(g['grant_address'].unique()))
    return (multiplier,)


@app.cell
def _(PURPLE, WHITE, g, plt):
    _fig, _ax = plt.subplots(figsize=(15, 5), facecolor=WHITE)
    g.groupby(['quarter', 'round'])['total_usd'].sum().iloc[:19].reset_index().set_index('round')['total_usd'].apply(int).plot(kind='bar', color=PURPLE, ax=_ax)
    _ax.set_facecolor(WHITE)
    plt.xticks(rotation=0)
    _ax.set_xlabel('')
    yticks = _ax.get_yticks()
    ylabels = [f'${y.get_text()}M' for y in _ax.get_yticklabels()]
    _ax.set_yticks(yticks, labels=ylabels)
    _ax.set_title('Amount raised per round (Gitcoin Grants program)', loc='left', weight='bold')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Four phases of grants""")
    return


@app.cell
def _(PURPLE, WHITE, g, np, plt):
    COLOR = PURPLE

    def phase_chart(dataframe):
        dff = dataframe[['project_name', 'amount_usd', 'match_usd', 'total_usd', 'round']].dropna().sort_values(by='total_usd', ascending=False)
        n = len(dff['total_usd'])
        total = dff['total_usd'].sum() / 1000000
        max_y = dff['total_usd'].iloc[1:].max()
        qf = dff[dff['match_usd'] > 0]['match_usd'].sum()
        rf = dff[dff['match_usd'] > 0]['amount_usd'].sum()
        multiple = rf / qf
        round_names = sorted(dff['round'].unique())
        title = f'Gitcoin Grants: {round_names[0]}-{round_names[-1]}'
        title += f'\nTotal = {total:,.1f}M DAI, QF multiplier = {multiple:,.2f}x'
        _fig, _ax = plt.subplots(figsize=(15, 5), facecolor=WHITE)
        (dff['total_usd'] / 1000).plot(kind='bar', lw=0, color=COLOR, edgecolor=COLOR, width=1)
        _ax.set_xlim(0, n)
        step = 10 ** int(np.log10(n))
        if n / step < 5:
            step = int(step / 2)
        xticks = [x for x in range(step, n, step)]
        _ax.set_xticks(xticks, xticks, rotation=0)
        _ax.set_xlabel('Num project applications')
        _ax.set_ylim(0, max_y / 1000)
        yticks = _ax.get_yticks()
        ylabels = [f'${y.get_text()}K' for y in _ax.get_yticklabels()]
        _ax.set_yticks(yticks, labels=ylabels)
        _ax.set_ylabel('Total funding per project (per round)')
        _ax.set_title(title, loc='left')
        short_tail = dff[dff['match_usd'] > 0].groupby('project_name')['total_usd'].sum().sort_values(ascending=False).head(10)
        projects = 'Top Projects:\n\n' + '\n'.join([f'- {p}' for p in short_tail.index.unique()])
        _ax.text(s=projects, x=n * 0.05, y=max_y / 1000, va='top')
        _ax.set_facecolor(WHITE)

        return _fig
    phase_chart(g[g['quarter'] < '2020Q1'])
    return (phase_chart,)


@app.cell
def _(g, phase_chart):
    phase_chart(g[(g['quarter'] >= '2020Q1') & (g['quarter'] < '2021Q2')])
    return


@app.cell
def _(g, phase_chart):
    phase_chart(g[(g['quarter'] >= '2021Q2') & (g['quarter'] < '2023Q1')])
    return


@app.cell
def _(g, phase_chart):
    phase_chart(g[(g['quarter'] >= '2023Q1') & (g['quarter'] < '2024Q1')])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Incorporate OSS Impact Data""")
    return


@app.cell
def _(DATA_URL_BASE, END, START, pd):
    # load and arrange the impact metrics
    impact = (
        pd.read_csv(f"{DATA_URL_BASE}/csv/gitcoin_active_devs_impact_by_quarter.csv", index_col=0)
        .set_index(['project_slug', 'quarter'])
        .join(
            pd.read_csv(f"{DATA_URL_BASE}/csv/gitcoin_contributor_impact_by_quarter.csv", index_col=0)
            .groupby(['project_slug', 'quarter'])
            ['from_name']
            .nunique()
            .rename('contributors')
        )
        .reset_index()
    )
    impact = impact[
        (impact['project_slug'] != 'gitcoin') 
        & (impact['quarter'] >= START) 
        & (impact['quarter'] <= END)
    ]

    # filter on the top 50 OSS projects
    top50_oss_slugs = (    
        impact
        .groupby('project_slug')
        ['contributors']
        .max()
        .sort_values()
        .tail(50)
        .index
        .to_list()
    )
    impact = impact[impact['project_slug'].isin(top50_oss_slugs)]
    impact.head(2)
    return impact, top50_oss_slugs


@app.cell
def _(g, top50_oss_slugs):
    # filter on the relevants grants data
    grants = g.copy()
    grants = grants[['oso_slug', 'round_id', 'round_name', 'quarter', 'round', 'round_date', 'total_usd']]
    grants = grants[grants['oso_slug'].isin(top50_oss_slugs)]
    grants.head(1)
    return (grants,)


@app.cell
def _(grants, impact, multiplier):
    # get ROI figures

    oss_grants = grants['total_usd'].sum()
    oss_devs = impact[impact['quarter'] == '2023Q4']['full-time'].sum()
    print("Cum. grants to top 50 OSS ($M):", oss_grants/1_000_000)
    print("Full-time developers at top 50 OSS (2023Q4):", oss_devs)
    roi = oss_devs/oss_grants*1_000_000
    print("$1M in grants gets __ full-time devs:", roi)
    print("... with crowdfunding multiplier:", roi*multiplier)
    return


@app.cell
def _(PURPLE, WHITE, impact, plt, project_names, sns):
    _fig, _ax = plt.subplots(figsize=(12, 5), facecolor=WHITE)
    impact.pivot_table(index='project_slug', columns='quarter', values='contributors').iloc[:, -4:].fillna(0).mean(axis=1).sort_values(ascending=False).rename(index=project_names).plot(kind='bar', color=PURPLE, ax=_ax)
    _ax.set_facecolor(WHITE)
    _ax.set_xlabel('')
    _ax.set_title('Avg quarterly contributors for the top 50 OSS projects on Gitcoin Grants in 2023', loc='left')
    sns.despine()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Make THE Graph""")
    return


@app.cell
def _(grants, impact):
    # have some quarterly stats ready to help with the plotting

    grant_stats = grants.groupby(['quarter', 'round'])['total_usd'].sum()

    quarters = sorted(impact['quarter'].unique())
    quarter_mapping = dict(zip(quarters, range(len(quarters))))

    projects_first_rounds = (
        grants
        .groupby(['oso_slug'])
        ['quarter']
        .min()
        .reset_index()
        .groupby('quarter')
        ['oso_slug']
        .agg(lambda x: sorted(x))
    )
    ordered_projects_list = [p for lst in projects_first_rounds for p in lst]
    projects_first_rounds.head(2)
    return (
        grant_stats,
        ordered_projects_list,
        projects_first_rounds,
        quarter_mapping,
    )


@app.cell
def _(
    END,
    GREEN,
    PURPLE,
    SMALL,
    START,
    WHITE,
    grant_stats,
    grants,
    impact,
    ordered_projects_list,
    plt,
    project_names,
    projects_first_rounds,
    quarter_mapping,
    sns,
):
    _fig, _ax = plt.subplots(figsize=(18, 10), dpi=144, facecolor=WHITE)
    start_q, end_q = (quarter_mapping.get(START), quarter_mapping.get(END))

    def plot_vector(col_name, col_label, color, ax):
        vector = impact.groupby('quarter')[col_name].sum()
        peak_impact = vector.max()
        scaled_vector = vector / vector[0]
        cagr = round(((vector[-1] / vector[0]) ** (1 / len(vector)) - 1) * 100, 1)
        scaled_vector.plot(kind='line', lw=4, color=color, alpha=0.75, ax=_ax)
        _ax.text(s='\n'.join([col_label, f'+{cagr}% growth (QoQ)', f'({vector[0]:,.0f} -> {vector[-1]:,.0f})']), x=end_q + 0.25, y=scaled_vector[-1], weight='bold', ha='left', va='center', color=GREEN)
    plot_vector('contributors', 'Contributors', '#A3E5E7', _ax)
    plot_vector('part-time', 'Part-time developers', PURPLE, _ax)
    plot_vector('full-time', 'Full-time developers', GREEN, _ax)
    _ax.set_ylim(1)
    ymax = _ax.get_ylim()[1]
    ysub = -(ymax * 0.1)
    ysub_offset = ymax * 0.0225
    _ax.text(s='Funding to top\n50 OSS projects\nby grants round', x=-0.25, y=ysub / 2, ha='left', va='center', fontsize=SMALL, color=GREEN, weight='bold')
    amt_fmt = lambda a: '<$0.1M' if a < 100000 else f'${a / 1000000:.1f}M'
    amt_fmt_k = lambda a: '<$1K' if a < 1000 else f'${a / 1000:.0f}K'
    for i, ((quarter, round_name), amount) in enumerate(grant_stats.items()):
        x = quarter_mapping.get(quarter)
        if not x:
            continue
        _ax.axvline(x=x, ymin=0, ymax=0.95, color=GREEN, lw=0.5, alpha=0.5)
        amt = amt_fmt(amount)
        label = f'{round_name}\n{amt}'
        _ax.text(s=label, x=x, y=ysub / 2, ha='center', va='center', fontsize=SMALL, color=GREEN, weight='bold')
        first_round_projects = projects_first_rounds.get(quarter)
        for y, project_slug in enumerate(ordered_projects_list):
            filtered_grants = grants[grants['quarter'] == quarter]
            included_projects = filtered_grants['oso_slug'].to_list()
            if project_slug not in included_projects:
                continue
            if first_round_projects and project_slug in first_round_projects:
                _ax.text(s=f'{project_names[project_slug]} ', x=x - 0.25, y=ysub - y * ysub_offset, color=GREEN, weight='bold', ha='right')
            result = filtered_grants[filtered_grants['oso_slug'] == project_slug]['total_usd'].sum()
            label = amt_fmt_k(result)
            _ax.text(s=label, x=x, y=ysub - y * ysub_offset, color='grey', alpha=0.5, ha='center')
    interval = 4
    quarters_list = list(quarter_mapping.keys())
    _ax.set_xlim(start_q, end_q + 0.25)
    xs = list(range(0, len(quarters_list), interval))
    _ax.set_xticks(xs)
    _ax.set_xticklabels([str(x) for x in range(2018, 2024)], weight='bold')
    _ax.text(s=f'Total\n{amt_fmt(grant_stats.sum())}', x=end_q + 2, y=ysub / 2, weight='bold', ha='right', va='center', color=GREEN)
    for y, project_slug in enumerate(ordered_projects_list):
        funding = grants[grants['oso_slug'] == project_slug]['total_usd'].sum()
        _ax.text(s=f'{amt_fmt_k(funding)}', x=end_q + 2, y=ysub - y * ysub_offset, ha='right', color=GREEN)
    _ax.set_xlabel('')
    _ax.set_ylabel('')
    _ax.set_yticks([2, 5, 10, 15, 20])
    _ax.set_yticklabels(['2x', '5x', '10x', '15x', '20x'])
    _ax.set_facecolor(WHITE)
    _ax.text(s='Grants = Growth', x=0, y=ymax * 1.04, weight='bold', fontsize=18)
    _ax.set_title('Quarterly developer metrics for the top 50 OSS projects on Gitcoin Grants since 2018', loc='left')
    sns.despine()
    #_fig.savefig('gitcoin_grants_growth.png', dpi=144)
    _fig
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
