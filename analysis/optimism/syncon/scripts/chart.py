import plotly.graph_objects as go
from plotly.subplots import make_subplots

def make_linechart(
        df, 
        title, 
        treatment_label='Treatment', 
        events=[], 
        event_line_color='rgba(0, 0, 0, 0.5)',
        shade_color='rgba(255, 4, 32, 0.1)',
        layout_kwargs={}
        ):

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df[df['cohort'] == 'treatment']['value'],
            name=treatment_label,
            line=dict(color='#ff0420', width=2),
            mode='lines'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df[df['cohort'] == 'synthetic']['value'],
            name='Synthetic Control',
            line=dict(color='gray', width=2),
            mode='lines'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df[df['cohort'] == 'treatment']['value'],
            fill=None,
            mode='lines',
            line=dict(width=0),
            showlegend=False
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df[df['cohort'] == 'synthetic']['value'],
            fill='tonexty',
            mode='lines',
            line=dict(width=0),
            fillcolor=shade_color,
            showlegend=False
        )
    )

    for event in events:
        fig.add_vline(
            x=event['date'],
            line_dash="dash",
            line_color=event_line_color,
            line_width=1
        )
        
        fig.add_annotation(
            x=event['date'],
            y=1,
            yref='paper',
            text=event['text'],
            showarrow=False,
            textangle=0,
            font=dict(size=10),
            xanchor='center',
            yanchor='bottom'
        )


    fig.update_layout(
        title=title,
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=True,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='black',
            linewidth=1,
            ticks='outside',
            tickcolor='black',
            tickwidth=1
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='black',
            linewidth=1,
            ticks='outside',
            tickcolor='black',
            tickwidth=1
        ),
    
        margin=dict(t=100)
    )
    fig.update_layout(layout_kwargs)

    fig.show()