import plotly.express as px
import pandas as pd
import numpy as np

MAIN_COLOR = "#FF0420"
MED_COLOR = "#FF6969"
LIGHT_COLOR = "#FFCCDD"


def make_sankey_graph(
    df, 
    cat_cols, 
    value_col,
    title,
    width=1000, 
    height=800, 
    size=12,
    decimals=True,
    hide_label_cols=[]):

    # build the title info
    total = df[value_col].sum()
    max_nodes = max(df[cat_cols].nunique())
    line_width = min(.5, (height / max_nodes / 50))

    # make the Sankey
    labelList = []
    nodeLabelList = []
    colorNumList = []
    for catCol in cat_cols:
        labelListTemp = list(set(df[catCol].values))        
        colorNumList.append(len(labelListTemp))
        labelList = labelList + labelListTemp
        if catCol in hide_label_cols:
            nodeLabelList = nodeLabelList + [""] * len(labelListTemp)
        else:
            nodeLabelList = nodeLabelList + labelListTemp

    # remove duplicates from labelList
    labelList = list(dict.fromkeys(labelList))

    # define colors based on number of categories
    colorPalette = [MAIN_COLOR, MED_COLOR, LIGHT_COLOR]
    colorList = []
    for idx, colorNum in enumerate(colorNumList):
        colorList = colorList + [colorPalette[idx]]*colorNum

    # transform df into a source-target pair
    for i in range(len(cat_cols)-1):
        if i==0:
            sourceTargetDf = df[[cat_cols[i], cat_cols[i+1], value_col]]
            sourceTargetDf.columns = ['source','target','value']
        else:
            tempDf = df[[cat_cols[i],cat_cols[i+1],value_col]]
            tempDf.columns = ['source','target','value']
            sourceTargetDf = pd.concat([sourceTargetDf,tempDf])
        sourceTargetDf = sourceTargetDf.groupby(['source','target']
            ).agg({'value':'sum'}).reset_index()

    # add index for source-target pair
    sourceTargetDf['sourceID'] = sourceTargetDf['source'].apply(
        lambda x: labelList.index(x))
    sourceTargetDf['targetID'] = sourceTargetDf['target'].apply(
        lambda x: labelList.index(x))

    linkLabels = []
    for c in cat_cols:
        linkLabels += [c] * df[c].nunique()

    # creating the sankey diagram
    pad = 15
    node_thickness = 10
    data = dict(
        type='sankey',
        orientation='h',
        domain=dict(x=[0,1], y=[0,1]),
        arrangement='freeform', #'snap',
        node=dict(
          thickness=node_thickness,
          line=dict(color=MAIN_COLOR, width=line_width),
          label=nodeLabelList,
          color=colorList,
          customdata=linkLabels,
          hovertemplate="<br>".join([
                "<b>%{value:,.1f}</b>" if decimals else "<b>%{value:,.0f}</b>",
                "%{customdata}: %{label}",
                "<extra></extra>"
            ])
        ),
        link=dict(
          source=sourceTargetDf['sourceID'],
          target=sourceTargetDf['targetID'],
          value=sourceTargetDf['value'],
          hovertemplate="<br>".join([
                "<b>%{value:,.1f}</b>" if decimals else "<b>%{value:,.0f}</b>",
                "%{source.customdata}: %{source.label}",
                "%{target.customdata}: %{target.label}",
                "<extra></extra>"
            ])
        )
      )

    xpad = ((node_thickness+pad)/2)/width
    xpos = np.linspace(xpad, 1-xpad, len(cat_cols))

    layout = dict(
        title=dict(text=title, x=0, xref='paper', xanchor = "left"),
        font=dict(color=MAIN_COLOR, size=size), #family="Arial"
        autosize=True,
        height=height,
        annotations=[
            dict(
                text=f"<br><b>{cat}</b>",
                x=xpos[i], xref='paper', xanchor='center',                 
                y=1, yref='paper', yanchor='bottom',                 
                font=dict(color=MAIN_COLOR, size=size+2),
                align='center', showarrow=False
            )
            for i, cat in enumerate(cat_cols)
        ]
    )
    fig = dict(data=[data], layout=layout)
    return fig