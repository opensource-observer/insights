import matplotlib.pyplot as plt
import pandas as pd

EVENT_TYPES = [
    'COMMIT_CODE',        
     'PULL_REQUEST_CREATED',
#     'PULL_REQUEST_MERGED',
#     'PULL_REQUEST_CLOSED',
     'PULL_REQUEST_APPROVED',
     'ISSUE_CLOSED',
     'ISSUE_CREATED'
]

def activity_plot(
    dataframe,
    grouper_col,
    date_col='date',
    value_col='num_contributions',
    filter_col='event_type',
    filter_vals=EVENT_TYPES,
    ylabel='Total Contributions',
    start_date=None,
    end_date=None
    ):


    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)

    dff = dataframe[dataframe[filter_col].isin(filter_vals)]
    pivot_df = (dff
                .groupby([date_col, grouper_col])[value_col]
                .sum().reset_index()
                .pivot(index=date_col, columns=grouper_col, values=value_col)
                .fillna(0))

    col_order = list(dff.groupby(grouper_col)[date_col].min().sort_values().index)
    ax.stackplot(pivot_df.index.to_timestamp(), pivot_df[col_order].values.T, labels=col_order)
    
    if start_date is None:
        start_date = pivot_df.index.min()
    else:
        start_date = pd.to_datetime(start_date)
    if end_date is None:
        end_date = pivot_df.index.max()
    else:
        end_date = pd.to_datetime(end_date)
    ax.set_xlim(start_date, end_date)
    
    ax.set_xlabel('')
    ax.set_ylabel(ylabel)
    ax.legend(loc='upper left')
    plt.xticks(rotation=0)
    
    return fig, ax