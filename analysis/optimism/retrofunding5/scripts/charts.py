import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Color definitions
COLOR1 = "#FF0420"
COLOR2 = "#FF6969"
COLOR3 = "#FFCCDD"

# Font size definitions
TITLE_SIZE = 16
FONT_SIZE = 14
SMALLER_FONT_SIZE = 10

IMAGE_WIDTH = 10
IMAGE_HEIGHT = 3

# Matplotlib configuration
plt.rcParams.update({
    'figure.dpi': 300,
    'figure.facecolor': 'white',
    'axes.spines.right': False,
    'axes.spines.top': False,
    'font.family': 'Arial',
    'font.size': FONT_SIZE,
    'axes.titlesize': FONT_SIZE,
    'axes.labelsize': FONT_SIZE,
    'xtick.labelsize': FONT_SIZE,
    'ytick.labelsize': FONT_SIZE,
    'legend.fontsize': FONT_SIZE,
    'legend.title_fontsize': FONT_SIZE,
    'figure.titlesize': TITLE_SIZE,
    'figure.titleweight': 'bold',
})


def get_plot(data, **kwargs):
    fig, ax = plt.subplots(figsize=(IMAGE_WIDTH, IMAGE_HEIGHT))
    data.plot(ax=ax, **kwargs)
    return fig, ax


def distributions_barchart(series, title, xstep=5, ystep=100, ymax=400):
    fig, ax = plt.subplots(figsize=(IMAGE_WIDTH, 3))
    series = series.sort_values(ascending=False) / 1000
    series.plot(kind='bar', color=COLOR1, alpha=.5, ax=ax, width=1)
    xmax = len(series)

    format_axis(
        ax,
        xmin=0, 
        xmax=xmax, 
        xstep=xstep, 
        ymax=ymax, 
        ystep=ystep,
        ypost="K",
        yfmt=".0f"
    )
    
    ax.set_xlabel("Project Rank")
    ax.tick_params(axis='x', rotation=0)
    ax.set_ylabel("Funding (OP)")
    
    med = series.median()
    ax.axhline(med, color='grey', linestyle='--', lw=1)
    ax.text(s=f"Median: {med:.0f}K OP", x=xmax, y=med, va='bottom', ha='right')    
    
    top10 = series.quantile(.9)
    ax.axhline(top10, color='grey', linestyle='--', lw=1)
    ax.text(s=f"Top 10%: {top10:.0f}K OP", x=xmax, y=top10, va='bottom', ha='right')    
    
    ax.set_title(f"{title}\n", loc='left', weight='bold')
    sns.despine()
    fig.tight_layout()
    return fig


def stripplot(unstacked_df, x, y, hue, row_div=4, **kwargs):
    num_rows = unstacked_df[y].nunique()
    fig, ax = plt.subplots(figsize=(10, num_rows // row_div), dpi=300)
    sns.stripplot(
        data=unstacked_df,
        x=x,
        y=y,
        hue=hue,
        orient='h',
        jitter=0,
        ax=ax,
        **kwargs
    )
    ax.grid(color='grey', linestyle='--', linewidth=.5)       
    ax.spines[['right', 'top', 'left', 'bottom']].set_visible(False)
    ax.tick_params(direction='out', length=0, width=.5, grid_alpha=0.5)
    ax.set_xlabel("")
    ax.set_ylabel("")
    return fig, ax


def format_axis(
    ax,
    xmin=None,
    xmax=None,
    xstep=None,
    ymax=None,
    ystep=None,
    xfmt=None,
    yfmt=None,
    xpost=None,
    ypost=None
):
    if xmin is not None or xmax is not None:
        ax.set_xlim(xmin, xmax)
    
    if xstep is not None:
        xticks = np.arange(xmin if xmin is not None else 0, xmax + xstep, xstep)
        ax.set_xticks(xticks)        
        if isinstance(xfmt, str):
            xtick_labels = [format(tick, xfmt) for tick in xticks]
        elif callable(xfmt):
            xtick_labels = [xfmt(tick) for tick in xticks]
        else:
            xtick_labels = [str(tick) for tick in xticks]

        if xpost:
            xtick_labels[-1] += f"{xpost}"
        ax.set_xticklabels(xtick_labels)
    if xpost is not None and not ax.get_xlabel():
        ax.set_xlabel(xpost)

    if ymax is not None:
        ax.set_ylim(0, ymax)
    if ystep is not None:
        yticks = np.arange(0, ymax + ystep, ystep)
        ax.set_yticks(yticks)        
        if isinstance(yfmt, str):
            ytick_labels = [format(tick, yfmt) for tick in yticks]
        elif callable(yfmt):
            ytick_labels = [yfmt(tick) for tick in yticks]
        else:
            ytick_labels = [str(tick) for tick in yticks]
        if ypost:
            ytick_labels[-1] += f"{ypost}"
        ax.set_yticklabels(ytick_labels)
    if ypost is not None and not ax.get_ylabel():
        ax.set_ylabel(ypost)

    return ax


def plot_ballots_by_project_category(
    unstacked_votes,
    xcol,
    ycol='project_name',
    subtitle=''):
    
    if xcol == 'project_percentage':
        xmax = 12.5
        scale_factor = 100
        xpost = '%'
        xstep = 2.5
        round_func = lambda x: round(x,1)
    else:
        xmax = 200
        scale_factor = 1/1000.
        xpost = 'K'
        xstep = 40
        round_func = lambda x: round(x,0)
    
    n = unstacked_votes[ycol].nunique()
    v = unstacked_votes['voter_address'].nunique()

    median = unstacked_votes.groupby(ycol)[xcol].median() * scale_factor
    stdev = unstacked_votes.groupby(ycol)[xcol].std() * scale_factor
    
    clipped_votes = unstacked_votes.copy()
    clipped_votes[xcol] = np.clip(clipped_votes[xcol] * scale_factor, 0, xmax)
    
    sorted_median = median.sort_values(ascending=False)
    clipped_votes[ycol] = pd.Categorical(clipped_votes[ycol], categories=sorted_median.index, ordered=True)
    clipped_votes = clipped_votes.sort_values(by=ycol)
    
    fig, ax = stripplot(
        unstacked_df=clipped_votes,
        x=xcol,
        y=ycol,
        hue=xcol,
        row_div=4,
        hue_norm=(0, xmax),
        palette="flare",
        alpha=.25,
        linewidth=0,
        size=10,
        legend=False
    )
    ax.set_xlabel(" ")
    format_axis(ax, xmin=0, xmax=xmax, xstep=xstep, xpost=f"{xpost}+")
    ax.set_xlim(-xmax*.02, xmax*1.02)
    
    yticks = []
    for lbl in ax.get_yticklabels():
        p = lbl.get_text()
        y = lbl.get_position()[1]
        m = round_func(median.get(p))
        s = round_func(stdev.get(p))
        txt = f"Median: {m}{xpost}, Std: {s}{xpost}"
        ax.text(s=txt, x=xmax*1.03, y=y, ha='left', va='center')

    ax.set_title(f"{subtitle} ({n} projects, {v} voters)\n", loc='left', weight='bold')
    
    fig.tight_layout()
    return fig


def plot_medians_by_voter_group(
    unstacked_votes,
    xcol,
    ycol='project_name',
    group_col='expertise_group',
    subtitle=''):
    

    order = list(sorted(unstacked_votes[group_col].unique()))
    colors = ['black', '#DDD']
    palette = dict(zip(order,colors))
    
    if xcol == 'project_percentage':
        xmax = 10
        scale_factor = 100
        xpost = '%'
        xstep = 2
        round_func = lambda x: round(x,1)
    else:
        xmax = 200
        scale_factor = 1/1000.
        xpost = 'K'
        xstep = 40
        round_func = lambda x: round(x,0)
    
    n = unstacked_votes[ycol].nunique()
    v = unstacked_votes['voter_address'].nunique()
    median = unstacked_votes.groupby(ycol)[xcol].median() * scale_factor
    sorted_median = median.sort_values(ascending=False)
    
    grouped_votes_series = (
        unstacked_votes.groupby([group_col, ycol])[xcol].median() * scale_factor
    )
    
    grouped_votes = grouped_votes_series.reset_index()
    grouped_votes[ycol] = pd.Categorical(grouped_votes[ycol], categories=sorted_median.index, ordered=True)
    grouped_votes = grouped_votes.sort_values(by=ycol)
    
    fig, ax = stripplot(
        unstacked_df=grouped_votes,
        x=xcol,
        y=ycol,
        hue=group_col,
        row_div=3,
        hue_order=order,
        palette=palette,
        linewidth=1,
        edgecolor='black',
        size=8,
        legend=True
    )
    ax.set_xlabel(" ")
    format_axis(ax, xmin=0, xmax=xmax, xstep=xstep, xpost=f"{xpost}")
    ax.set_xlim(-xmax*.02, xmax*1.02)
    
    for lbl in ax.get_yticklabels():
        p = lbl.get_text()
        y = lbl.get_position()[1]
        
        x1 = grouped_votes_series.loc[(order[0], p)]
        x2 = grouped_votes_series.loc[(order[1], p)]
        if (xcol == 'project_percentage' and abs(x1-x2) > 1) or (xcol == 'project_amount' and abs(x1-x2) > 12.5):
            facecolor = 'white' if x1 > x2 else "#FFCCDD"
            txt = f"{round_func(x1-x2):+}{xpost}"
            ax.text(
                s=txt, x=(x1+x2)/2, y=y, ha='center', va='center', #fontsize=SMALLER_FONT_SIZE, 
                bbox=dict(facecolor=facecolor, alpha=1, edgecolor='black', lw=.5)
            )
        ax.plot([x1, x2], [y, y], color='black', linewidth=0.8)

    ax.legend(loc='upper left')
    ax.set_title(f"{subtitle} ({n} projects, {v} voters)\n", loc='left', weight='bold')
    fig.tight_layout()


def category_kde_plots(df_category_votes, category):

    fig, ax = plt.subplots(figsize=(IMAGE_WIDTH, 3), dpi=300)
    dff = df_category_votes.copy()
    dff['Category Assignment'] = dff['category_assignment'].apply(lambda x: category if x == category else 'Other')
    palette = {category: COLOR1, 'Other': "#DDD"}
    sns.kdeplot(
        data=dff,
        x=category,
        hue='Category Assignment',
        hue_order=[category, 'Other'],
        palette=palette,
        fill=True,
        common_norm=False,
        bw_adjust=0.5,
        ax=ax
    )
    format_axis(ax, xmin=0, xmax=100, xpost='%')
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.spines['left'].set_visible(False)
    ax.set_yticks([])
    ax.set_title(f"Share of total budget that should go to {category}\n", loc='left', weight='bold')
    return fig, ax