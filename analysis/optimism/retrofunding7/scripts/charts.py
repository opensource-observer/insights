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
