import pandas as pd
import streamlit as st
import plotly.express as px


# highlight the cells based on the increase or decrease condition
def highlight_changes(val):
    if val == "increase":
        return 'background-color: green'
    elif val == "decrease":
        return 'background-color: red'
    return ''

# create the high level overview table of all of the projects
def high_level_overview_table(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    # flatten the column names to simplify processing
    df = df.copy()
    df.columns = [f"{col[0]}: {col[1]}" for col in df.columns]

    # initialize a dictionary to hold the simplified columns
    simplified_data = {
        "Project Name": df["General Info: Project Name"],
        "Round": df["General Info: Round"],
        "Cycle": df["General Info: Cycle"],
        "Status": df["General Info: Status"],
        "Amount": df["General Info: Amount"],
        "Date Range": df["General Info: Date Range"],
    }

    # process each metric to create a single column summarizing the result
    metric_list = ["Transaction Count", "Active Users", "Unique Users", "Total Transferred", "Net Transferred", "TVL"]

    for metric in metric_list:
        percent_change_col = f"{metric}: Percent Change"
        p_value_col = f"{metric}: P Value"

        # apply logic to categorize results based on percent change and p value
        simplified_data[metric] = df.apply(
            lambda row: (
                "N/A" if row[percent_change_col] == "N/A" or row[p_value_col] == "N/A" or pd.isna(row[percent_change_col]) or pd.isna(row[p_value_col]) else
                "decrease" if row[percent_change_col] < 0 and row[p_value_col] < alpha else
                "increase" if row[percent_change_col] > 0 and row[p_value_col] < alpha else
                "no change"
            ),
            axis=1
        )

    # create a new DataFrame with the simplified structure
    simplified_df = pd.DataFrame(simplified_data)
    simplified_df = simplified_df.T
    simplified_df.columns = simplified_df.iloc[0]
    simplified_df = simplified_df.iloc[1:]

    return simplified_df

# flatten and prepare the dataframe for the scatterplots
def prepare_data_for_scatterplots(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    # flatten the column names to simplify processing
    df = df.copy()
    df.columns = [f"{col[0]}: {col[1]}" for col in df.columns]
    
    # define the list of metrics
    metric_list = ["Transaction Count", "Active Users", "Unique Users", "Total Transferred", "Net Transferred", "TVL"]

    # select relevant columns
    target_cols = ["General Info: Project Name", "General Info: Amount"]
    for metric in metric_list:
        target_cols.append(f"{metric}: P Value")
        target_cols.append(f"{metric}: Percent Change")

    # keep only the target columns
    df = df[target_cols]

    # rename columns with distinct names for P Value and Percent Change
    rename_dict = {"General Info: Project Name": "Project", "General Info: Amount": "Grant Amount"}
    rename_dict.update({f"{metric}: P Value": f"{metric} P Value" for metric in metric_list})
    rename_dict.update({f"{metric}: Percent Change": f"{metric} Percent Change" for metric in metric_list})
    df.rename(columns=rename_dict, inplace=True)

    # melt the dataframe to combine all metrics into rows
    df = df.melt(
        id_vars=["Project", "Grant Amount"],
        value_vars=[f"{metric} P Value" for metric in metric_list] + [f"{metric} Percent Change" for metric in metric_list],
        var_name="Metric",
        value_name="Value"
    )

    # separate the Metric Type (P Value or Percent Change) and clean Metric names
    df["Metric Type"] = df["Metric"].apply(lambda x: "P Value" if "P Value" in x else "Percent Change")
    df["Metric"] = df["Metric"].str.replace(" P Value", "").str.replace(" Percent Change", "")

    # pivot the DataFrame to have P Value and Percent Change as columns
    df = df.pivot(index=["Project", "Grant Amount", "Metric"], columns="Metric Type", values="Value").reset_index()

    # drop rows with missing values
    df.dropna(subset=["Percent Change", "P Value"], inplace=True)

    # add a new column 'Change' based on Percent Change and P Value
    df["Change"] = df.apply(
        lambda row: (
            "decrease" if row["Percent Change"] < 0 and row["P Value"] < alpha else
            "increase" if row["Percent Change"] > 0 and row["P Value"] < alpha else
            "no change"
        ),
        axis=1
    )

    # keep only the required columns
    df = df[["Project", "Grant Amount", "Metric", "Percent Change", "P Value", "Change"]]

    return df

# display the 2 metric-specific impact scatterplots
def display_scatterplots(df: pd.DataFrame, alpha: float) -> None:
    st.subheader("Impact Across Projects By Metric")
    
    metric_list = ["Transaction Count", "Active Users", "Unique Users", "Total Transferred", "Net Transferred", "TVL"]
    selected_metric = st.selectbox("Select desired metric", metric_list)

    df = df[df["Metric"] == selected_metric]

    # determine the max range for x-axis (symmetric around 0)
    df["Percent Change"] *= 100
    max_percent_change = max(abs(df["Percent Change"].min()), abs(df["Percent Change"].max()))
    x_range = [-max_percent_change, max_percent_change]

    # define custom color mapping
    color_map = {
        "increase": "green",  
        "decrease": "red",    
        "no change": "rgba(128, 128, 128, 0.6)"
    }

    fig1 = px.scatter(
        df,
        x="Percent Change",  # use numeric Percent Change for proper axis scaling
        y="P Value",
        color="Change",  # column indicating increase, decrease, or no change
        color_discrete_map=color_map,  # apply custom colors
        title="Significance and Impact of the Grant on Each Project",
        text="Project",
        labels={"Percent Change": "Percent Change (%)", "P Value": "Significance"}
    )

    # update trace to position text and adjust marker size
    fig1.update_traces(
        textposition="top center",  # position text above the dots
        marker=dict(size=10)  # increase dot size
    )

    # add a horizontal dashed line for significance level
    fig1.add_hline(
        y=alpha, 
        line_width=2, 
        line_dash="dash", 
        line_color="red"
    )

    # add shaded regions
    fig1.add_shape(
        type="rect",
        x0=-max_percent_change,  # start of shaded region on x-axis
        x1=max_percent_change,  # end of shaded region on x-axis
        y0=alpha,  # gottom of shaded region
        y1=1,  # top of shaded region (P Value range is assumed to be 0-1)
        fillcolor="rgba(0, 0, 0, 0.1)",  # semi-transparent gray
        layer="below",  # place below the data points
        line_width=0  # no border for the rectangle
    )

    fig1.add_shape(
        type="rect",
        x0=-max_percent_change,  # start of shaded region on x-axis
        x1=max_percent_change,  # end of shaded region on x-axis
        y0=0,  # bottom of shaded region
        y1=alpha,  # top of shaded region (P Value range is assumed to be 0-1)
        fillcolor="rgba(256, 256, 256, 0.05)",  # semi-transparent white
        layer="below",  # place below the data points
        line_width=0  # no border for the rectangle
    )

    # add annotations for "Not Significant" and "Significant" labels
    fig1.add_annotation(
        x=1.03,  # position outside the graph on the right side
        y=(alpha + 1) / 2,  # middle of the "Not Significant" region
        text="Not Significant", 
        showarrow=False, 
        font=dict(size=14, color="white"),  
        align="center",
        textangle=90,  # rotate 90 degrees clockwise (top facing the graph)
        xref="paper",  # use relative position (outside the plot area)
        yref="y"  # align to the y-axis
    )

    fig1.add_annotation(
        x=1.03,  # position outside the graph on the right side
        y=alpha / 2,  # middle of the "Significant" region
        text="Significant", 
        showarrow=False, 
        font=dict(size=14, color="white"), 
        align="center",
        textangle=90,  # rotate 90 degrees clockwise (top facing the graph)
        xref="paper",  # use relative position (outside the plot area)
        yref="y"  # align to the y-axis
    )

    # adjust plot layout
    fig1.update_layout(
        margin=dict(
            r=30
        ),
        xaxis=dict(range=x_range),  # set symmetric x-axis range
        width=900,  # set plot width
        height=600,  # set plot height
        title_font=dict(size=20),  # adjust title font size
        xaxis_title_font=dict(size=16),  # adjust x-axis label font size
        yaxis_title_font=dict(size=16),  # adjust y-axis label font size
        legend_title="",
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    st.plotly_chart(fig1)

    fig2 = px.scatter(
        df,
        x="Grant Amount",
        y="Percent Change",
        color="Change",
        color_discrete_map=color_map,
        title="Impact of Each Project by Grant Amount",
        text="Project",
        labels={"Grant Amount": "Grant Amount ($)", "Percent Change": "Percent Change (%)"}
    )

    # update trace to position text and adjust marker size
    fig2.update_traces(
        textposition="top center",  # position text above the dots
        marker=dict(size=10)  # increase dot size
    )

    # adjust plot layout
    fig2.update_layout(
        width=900,  # set plot width
        height=600,  # set plot height
        title_font=dict(size=20),  # adjust title font size
        xaxis_title_font=dict(size=16),  # adjust x-axis label font size
        yaxis_title_font=dict(size=16),  # adjust y-axis label font size
        legend_title="",
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    st.plotly_chart(fig2)

# display a bar chart of measured change by metric
def display_stacked_bar_chart(df: pd.DataFrame) -> None:
    # group the data and calculate percentages
    df_grouped = (
        df.groupby(["Metric", "Change"])
        .agg(
            Count=("Project", "size"),  
            Projects=("Project", lambda x: ", ".join(x))  # concatenate project names
        )
        .reset_index()
    )

    # calculate the percentage distribution
    total_counts = df_grouped.groupby("Metric")["Count"].transform("sum")
    df_grouped["Percentage"] = (df_grouped["Count"] / total_counts) * 100

    # define custom color mapping for the "Change" column
    color_map = {
        "increase": "green",
        "decrease": "red",
        "no change": "rgba(128, 128, 128, 0.6)"
    }

    # create the horizontal stacked bar chart
    fig = px.bar(
        df_grouped,
        x="Percentage",
        y="Metric",
        color="Change",
        orientation="h",  
        color_discrete_map=color_map,  
        title="Distribution of Changes by Metric",
        labels={"Percentage": "Percentage (%)", "Metric": " "},
        hover_data={"Projects": True, "Count": True}  # add projects and count to hover
    )

    fig.update_layout(
        barmode="stack",  # stacked bars
        xaxis=dict(title="Percentage (%)", tickformat=".1f"),  # format x-axis as percentages
        title_font=dict(size=20), 
        xaxis_title_font=dict(size=16),  
        yaxis_title_font=dict(size=16),  
        template="plotly_white", 
        legend_title="Change",
    )

    st.plotly_chart(fig)

# display all of the tables and visualizations that compare impact across all projects
def all_projects_section(ttest_results: pd.DataFrame, ):
    st.subheader("High-Level of All Projects")
    
    # allow users to manually set their desired alpha value
    alpha = st.slider(
        label="Select an alpha value",
        min_value=0.01,
        max_value=0.99,
        value=0.05,  # default value
        step=0.01,  # step size
        key="all_projects_alpha"
    )

    st.markdown(f"#### This means that we are ***{round((1 - (alpha)) * 100, 4)}%*** confident in our results.")

    st.divider()

    # flatten the data so it can be easily graphed
    simplified_project_table = prepare_data_for_scatterplots(ttest_results, alpha=alpha)

    # create and display the high level table
    table = high_level_overview_table(df=ttest_results, alpha=alpha)
    table.rename_axis("", inplace=True)
    styled_table = table.style.applymap(highlight_changes)  # highlight only metric columns
    st.dataframe(
        styled_table, 
        height=35*len(table)+38,
        column_config={
            project: st.column_config.TextColumn(width="medium")
            for project in list(table.columns) + [""]
        }
    )    

    st.divider()

    # display the 2 metric-specific impact scatterplots
    display_scatterplots(df=simplified_project_table, alpha=alpha)

    st.divider()

    # display a bar chart of measured change by metric
    display_stacked_bar_chart(df=simplified_project_table) 
    