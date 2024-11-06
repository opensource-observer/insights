import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Color definitions
COLOR1 = "#FF0420"
COLOR2 = "#FF6969"
COLOR3 = "#FFCCDD"

WHITE = '#FFFFFF'

# Font size definitions
TITLE_SIZE = 16
FONT_SIZE = 14
SMALLER_FONT_SIZE = 10

IMAGE_WIDTH = 10
IMAGE_HEIGHT = 3

# Matplotlib configuration
plt.rcParams.update({
    'figure.dpi': 300,
    'figure.facecolor': 'none',
    'axes.facecolor': 'none',
    'axes.spines.right': False,
    'axes.spines.top': False,
    'font.family': 'Helvetica',
    'font.size': FONT_SIZE,
    'axes.titlesize': FONT_SIZE,
    'axes.labelsize': FONT_SIZE,
    'xtick.labelsize': FONT_SIZE,
    'ytick.labelsize': FONT_SIZE,
    'text.color': WHITE,
    'axes.labelcolor': WHITE,
    'xtick.color': WHITE,
    'ytick.color': WHITE,
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
    ax.axhline(med, color=WHITE, linestyle='--', lw=1)
    ax.text(s=f"Median: {med:.0f}K OP", x=xmax, y=med, va='bottom', ha='right')    
    
    top10 = series.quantile(.9)
    ax.axhline(top10, color=WHITE, linestyle='--', lw=1)
    ax.text(s=f"Top 10%: {top10:.0f}K OP", x=xmax, y=top10, va='bottom', ha='right')    
    
    ax.set_title(f"{title}\n", loc='left', weight='bold')
    sns.despine()
    fig.tight_layout()
    return fig


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
