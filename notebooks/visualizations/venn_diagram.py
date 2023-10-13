import matplotlib.pyplot as plt
from matplotlib_venn import venn3, venn3_circles


DEFAULT_COLOR = "white"

def venn3_diagram(
    subsets, 
    labels,
    colors=[DEFAULT_COLOR,DEFAULT_COLOR,DEFAULT_COLOR],
    facecolor=DEFAULT_COLOR,
    dpi=144,
    fontsize=8,
    figsize=10):

    """
    Make a venn diagram with three sets.
    """
    
    plt.rcParams.update({'font.size': fontsize})
    fig, ax = plt.subplots(figsize=(figsize, figsize), dpi=dpi, facecolor=facecolor)        
    venn3(subsets=subsets, set_labels=labels, set_colors=colors, alpha=1, ax=ax)
    venn3_circles(subsets=subsets, linewidth=2)
    ax.set_facecolor(facecolor)
    
    return fig, ax