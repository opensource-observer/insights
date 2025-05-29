import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# helper function to format percent change
def format_percent_change(value: float) -> str:
    if abs(value) >= 1e6:  # use scientific notation for very large values
        return f"{value:.2e}"
    else:  # use standard formatting for smaller values
        return f"{value:.2f}"
    
# helper function to style cells in the second table
def style_table(row):
    return [
        'background-color: green; color: white' if isinstance(cell, str) and "increase" in cell else
        'background-color: red; color: white' if isinstance(cell, str) and "decrease" in cell else ''
        for cell in row
    ]


def high_level_overview_table(df: pd.DataFrame, alpha: float) -> None:
    
    st.markdown(
        """
        <p style="color: grey; font-style: italic;">
        Projects are ordered, left to right, based on the number of metrics that saw statistically significant increases
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Flatten the column names to simplify processing
    df = df.copy()
    df.columns = [f"{col[0]}: {col[1]}" for col in df.columns]

    # Initialize a dictionary to hold the simplified columns
    simplified_data = {
        "Project Name": df["General Info: Project Name"],
        "Round": df["General Info: Round"],
        "Cycle": df["General Info: Cycle"],
        "Grant Status": df["General Info: Grant Status"],
        "Grant Amount": df["General Info: Grant Amount"],
        "Grant Recieved (to date)?": df["General Info: Grant Recieved (to date)?"],
        "Date Funds Recieved": df["General Info: Date Funds Recieved"],
        "Balance Left (to date)": df["General Info: Balance Left (to date)"],
        "Date Range": df["General Info: Date Range"]
    }
    
    # define metric groups
    metric_list = ["Transaction Count", "Active Users", "Unique Users", "Total Transferred", "Net Transferred", "Retained Daily Active Users", "DAA/MAA", "Gas Fees"]

    # iterate over all metrics (including forecasted ones)
    for metric in metric_list:
        # check if the metric has a forecasted counterpart
        metric_variants = [metric, f"{metric} (forecasted)"]

        for curr_metric in metric_variants:
            # define column names for percent change and p-value
            percent_change_col = f"{curr_metric}: Percent Change"
            p_value_col = f"{curr_metric}: P Value"

            # apply logic to categorize results based on percent change and p-value
            simplified_data[curr_metric] = df.apply(
                lambda row: (
                    # handle cases where data is missing or invalid
                    "N/A" if row[percent_change_col] == "N/A" or row[p_value_col] == "N/A" or pd.isna(row[percent_change_col]) or pd.isna(row[p_value_col]) else
                    # format as a decrease if the percent change is negative and p-value is significant
                    f"-{format_percent_change(abs(row[percent_change_col] * 100))}% daily average decrease"
                    if row[percent_change_col] < 0 and row[p_value_col] < alpha else
                    # format as an increase if the percent change is positive and p-value is significant
                    f"+{format_percent_change(row[percent_change_col] * 100)}% daily average increase"
                    if row[percent_change_col] > 0 and row[p_value_col] < alpha else
                    # handle cases with no statistically significant change
                    "no statistically significant change"
                ),
                axis=1
            )

    # create a new dataframe with the simplified structure
    simplified_df = pd.DataFrame(simplified_data)
    simplified_df = simplified_df.T
    simplified_df.columns = simplified_df.iloc[0]
    simplified_df = simplified_df.iloc[1:]
    simplified_df = simplified_df.T

    # create a ranking dictionary to store mean percent change for each project
    ranking = {}
    for project_name, row in simplified_df.iterrows():
        cnt = 0
        for col in simplified_df.columns:
            if "increase" in str(row[col]):
                cnt += 1
        ranking[project_name] = cnt

    # rank projects based on mean percent change (highest to lowest)
    ranked_projects = sorted(ranking, key=ranking.get, reverse=True)

    # add projects not in ranking at the end
    all_projects = simplified_df.index.tolist()
    unranked_projects = [proj for proj in all_projects if proj not in ranking]
    final_project_order = ranked_projects + unranked_projects

    # reorder simplified_df based on ranking and transpose back
    simplified_df = simplified_df.loc[final_project_order].T

    # define each table
    project_details = simplified_df.iloc[:8]
    pre_grant_results = simplified_df[8:][~simplified_df[8:].index.str.contains(r"\(forecasted\)", regex=True)]
    forecasted_results = simplified_df[8:][simplified_df[8:].index.str.contains(r"\(forecasted\)", regex=True)]
    forecasted_results.index = forecasted_results.index.str.replace(" (forecasted)", "")

    st.markdown(
        """
        <style>
        .hypothesis-row {
            color: white;
            font-weight: bold;
            text-align: center;
            font-size: 20px;
            padding: 2px 0;
            margin: 2px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Display the first table
    st.dataframe(project_details, use_container_width=True)

    # Add a custom title for hypothesis testing
    st.markdown('<div class="hypothesis-row">How Post-Grant Performance Stacks up to Pre-Grant Data</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <p style="color: grey; font-style: italic;">
        The results below are based on a 2-sample T-Test, a statistical method used to compare the metrics and distributions of two samples. It evaluates whether each metric shows a statistically significant change between the pre-grant and post-grant periods.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Apply conditional formatting to the second table
    pre_grant_results_styled = pre_grant_results.style.apply(style_table, axis=1)
    st.dataframe(pre_grant_results_styled, use_container_width=True)

    st.markdown('<div class="hypothesis-row">How Post-Grant Performance Stacks up to Forecasted Data</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <p style="color: grey; font-style: italic;">
        This analysis also uses a 2-sample T-Test, but here the first sample is forecasted data. The forecast is generated using a SARIMA model, trained on trends from the pre-grant period. Additional details can be found in the Statistical Analysis section.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Apply conditional formatting to the second table
    forecasted_results_styled = forecasted_results.style.apply(style_table, axis=1)
    st.dataframe(forecasted_results_styled, use_container_width=True)


def by_protocol_table(df: pd.DataFrame, alpha: float) -> None:
    # dictionary to store results in the new format
    formatted_results = {}
    
    for _, row in df.iterrows():
        protocol = row['protocol']
        
        # process tvl results
        if row['TVL-pvalue'] < alpha:
            sign = "increase" if row['TVL-percent_change'] > 0 else "decrease"
            tvl_result = f"{format_percent_change(abs(row['TVL-percent_change'] * 100))}% daily average {sign}"
        else:
            tvl_result = "no statistically significant change"
        
        # process tvl_opchain results
        if row['TVL_opchain-pvalue'] < alpha:
            sign = "increase" if row['TVL_opchain-percent_change'] > 0 else "decrease"
            tvl_opchain_result = f"{format_percent_change(abs(row['TVL_opchain-percent_change'] * 100))}% daily average {sign}"
        else:
            tvl_opchain_result = "no statistically significant change"
        
        formatted_results[protocol] = {'Pre-Grant as Control Group': tvl_result, 'OP Chain Trends as Control Group': tvl_opchain_result}
    
    # create the formatted dataframe
    result_df = pd.DataFrame.from_dict(formatted_results, orient='index')
    result_df.index.name = 'Protocol'

    result_df_styled = result_df.style.apply(style_table, axis=1)
    st.dataframe(result_df_styled, height=29*len(df)+13, use_container_width=True)

    return


def display_north_star_metrics(df1: pd.DataFrame, df2: pd.DataFrame, alpha: float) -> None:
    st.markdown('<div class="hypothesis-row">North Star Metrics</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <p style="color: grey; font-style: italic;">
        The results below are based on a 2-sample T-Test, a statistical method used to compare the metrics and distributions of two samples. The synthetic control group for TVL is a linear regression model trained on trends from the entire OP Chain (additional details can be found in the Statistical Analysis section). The synthetic control group for other metrics are the period prior to the grant occurence.
        </p>
        """,
        unsafe_allow_html=True,
    )
    
    df1.rename(columns={"project":"Project", 
                        "north_star":"North Star", 
                        "synthetic_control_group":"Synthetic Control Group", 
                        "post_grant_actual":"Post Grant Actual",
                        "percent_change": "Percent Change"}, inplace=True)
    
    df1["North Star"] = df1["North Star"].replace({
        "active_users": "Daily Active Users",
        "transaction_cnt": "Daily Transactions",
        "gas_fee": "Daily Gas Fees",
        "new_delegators": "New Delegators",
        "new_voters": "New Voters"
    })

    df1_results = []
    for _, row in df1.iterrows():
        if row['p_value'] < alpha:
            sign = "increase" if row['Percent Change'] > 0 else "decrease"
            result = f"{format_percent_change(abs(row['Percent Change'] * 100))}% daily average {sign}"
        else:
            result = "no statistically significant change"
        df1_results.append(result)

    df1["Results"] = df1_results

    df1 = df1.drop(["p_value", "Percent Change"], axis=1)

    df2["Project"] = df2["project"] + ": '" + df2["protocol"] + "' defillama protocol"
    df2["North Star"] = "TVL"

    #df2.index = df2[['project', 'protocol']]
    df2 = df2.drop(["project", "protocol", 'north_star'], axis=1)
    df2.rename(columns={"synthetic_control_group":"Synthetic Control Group", 
                        "post_grant_actual":"Post Grant Actual",
                        "percent_change": "Percent Change"}, inplace=True)
    
    df2_results = []
    for _, row in df2.iterrows():
        if row['p_value'] < alpha:
            sign = "increase" if row['Percent Change'] > 0 else "decrease"
            result = f"{format_percent_change(abs(row['Percent Change'] * 100))}% daily average {sign}"
        else:
            result = "no statistically significant change"
        df2_results.append(result)

    df2["Results"] = df2_results

    df2 = df2.drop(["p_value", "Percent Change"], axis=1)

    concatted_df = pd.concat([df1, df2])

    concatted_df.index = concatted_df["Project"]
    concatted_df.drop("Project", axis=1, inplace=True)
    concatted_df["Results"].sort_values()

    # define a custom function to extract the numeric percentage
    def extract_percentage(val):
        if "increase" in val:
            return -float(val.split('%')[0])  # negate to sort descending
        elif "decrease" in val:
            return float(val.split('%')[0])
        else:
            return np.inf  # put "not statistically significant" at the bottom

    # apply the custom key function to create a sort key
    concatted_df['sort_key'] = concatted_df['Results'].apply(extract_percentage)

    # sort by the sort_key
    sorted_df = concatted_df.sort_values('sort_key')

    # drop the helper column if no longer needed
    sorted_df = sorted_df.drop(columns='sort_key')

    styled_concatted_df = sorted_df.style.apply(style_table)

    st.dataframe(styled_concatted_df, height=35*len(sorted_df)+38, use_container_width=True)

    return

# flatten and prepare the dataframe for the scatterplots
def prepare_data_for_scatterplots(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    # flatten the column names to simplify processing
    df = df.copy()
    df.columns = [f"{col[0]}: {col[1]}" for col in df.columns]
    
    # define the list of metrics
    metric_list = ["Transaction Count", "Active Users", "Unique Users", "Total Transferred", "Net Transferred", "Retained Daily Active Users", "DAA/MAA", "Gas Fees"]

    # select relevant columns
    target_cols = ["General Info: Project Name", "General Info: Grant Amount"]
    for metric in metric_list:
        target_cols.append(f"{metric}: P Value")
        target_cols.append(f"{metric}: Percent Change")

    # keep only the target columns
    df = df[target_cols]

    # rename columns with distinct names for P Value and Percent Change
    rename_dict = {"General Info: Project Name": "Project", "General Info: Grant Amount": "Grant Amount"}
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
            f"decrease" if row["Percent Change"] < 0 and row["P Value"] < alpha else
            f"increase" if row["Percent Change"] > 0 and row["P Value"] < alpha else
            "no change"
        ),
        axis=1
    )

    # keep only the required columns
    df = df[["Project", "Grant Amount", "Metric", "Percent Change", "P Value", "Change"]]

    return df

# display the 2 metric-specific impact scatterplots
def display_scatterplots(df: pd.DataFrame, tvl_df: pd.DataFrame, alpha: float) -> None:
    st.subheader("Impact Across Projects By Metric")

    metric_list = ["Transaction Count", "Active Users", "Unique Users", "Total Transferred", "Net Transferred", "Retained Daily Active Users", "DAA/MAA", "Gas Fees", "TVL"]
    selected_metric = st.selectbox("Select desired metric", metric_list)

    if selected_metric == "TVL":
        prv_df = df[["Project", "Grant Amount"]]
        df = tvl_df
        df.rename(columns={"percent_change":"Percent Change", "p_value": "P Value"}, inplace=True)

        conditions = [
            (df["P Value"] <= alpha) & (df["Percent Change"] > 0),
            (df["P Value"] <= alpha) & (df["Percent Change"] < 0),
        ]
        choices = ["increase", "decrease"]
        df["Change"] = np.select(conditions, choices, default="no change")
        df = pd.merge(df, prv_df, left_on="project", right_on="Project", how="left")
        df.rename(columns={"project":"Project"}, inplace=True)

    else:
        df = df[df["Metric"] == selected_metric]

    # ensure proper scaling
    df["Percent Change"] *= 100

    # handle negative values before applying log transformation
    offset = abs(df["Percent Change"].min()) + 1
    df["Percent Change"] += offset  # shift all values to make them positive
    df["Percent Change"] = np.log1p(df["Percent Change"])  # apply log transformation
    df["Percent Change"] -= np.log1p(offset)  # shift values back to their original range

    # determine x-axis range
    max_percent_change = max(abs(df["Percent Change"].min()), abs(df["Percent Change"].max()))

    # define color mapping
    color_map = {
        "increase": "green",
        "decrease": "red",
        "no change": "rgba(128, 128, 128, 0.6)"
    }

    # create scatter plot
    fig1 = px.scatter(
        df,
        x="P Value",
        y="Percent Change",
        color="Change",
        color_discrete_map=color_map,
        title="Significance and Impact of the Grant on Each Project",
        labels={"Percent Change": "Percent Change (Log Scale)", "P Value": "Significance"},
        hover_data={"Project": True, "Change": False, "P Value": False, "Percent Change": False} 
    )

    fig1.update_traces(
        textposition="middle right",
        marker=dict(size=12)
    )

    # add significance threshold and shaded regions
    fig1.add_vline(x=alpha, line_width=2, line_dash="dash", line_color="red")
    fig1.add_shape(type="rect", x0=alpha, x1=1, y0=-max_percent_change * 1.1, y1=max_percent_change * 1.1,
                   fillcolor="rgba(0, 0, 0, 0.3)", layer="above", line_width=0)
    fig1.add_shape(type="rect", x0=-0.01, x1=alpha, y0=-max_percent_change * 1.1, y1=max_percent_change * 1.1,
                   fillcolor="rgba(255, 255, 255, 0.1)", layer="below", line_width=0)

    # add annotations
    fig1.add_annotation(x=alpha + (1 - alpha) / 2, y= max_percent_change * 1.17, text="Not Significant",
                        showarrow=False, font=dict(size=14, color="white"), align="center")
    fig1.add_annotation(x=alpha / 2, y= max_percent_change * 1.17, text="Significant",
                        showarrow=False, font=dict(size=14, color="white"), align="center")

    # update layout
    fig1.update_layout(
        xaxis=dict(range=[-0.01, 1]),
        width=900,
        height=600,
        title_font=dict(size=20),
        xaxis_title_font=dict(size=16),
        yaxis_title_font=dict(size=16),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig1)

    fig2 = px.scatter(
        df,
        x="Grant Amount",
        y="Percent Change",
        color="Change",
        color_discrete_map=color_map,
        title="Impact of Each Project by Grant Amount",
        labels={"Grant Amount": "Grant Amount (OP)", "Percent Change": "Percent Change (Log Scale)"},
        hover_data={"Project": True, "Change": False, "P Value": False, "Percent Change": False} 
    )

    # update trace to position text and adjust marker size
    fig2.update_traces(
        textposition="top center",  # position text above the dots
        marker=dict(size=12)  # increase dot size
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
def all_projects_section(ttest_results: pd.DataFrame, tvl_ttest_results: pd.DataFrame, north_star_metrics: pd.DataFrame, tvl_north_star_metrics: pd.DataFrame) -> None:
    st.subheader("High-Level of All Projects")

    st.markdown(
        """
        <p style="color: grey; font-style: italic;">
        Begin by defining an alpha value, which represents the confidence level in the statistical results. Metrics with p-values exceeding this threshold will be deemed not statistically significant. Increasing the alpha value reduces the confidence level but allows more results to be classified as statistically significant, providing greater flexibility at the expense of precision.
        </p>
        """,
        unsafe_allow_html=True,
    )
    
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

    by_project, by_protocol, north_star = st.tabs(["View By Project", "View By Protocol", "North Star Metrics"])
    with by_project:
        # create and display the high level table
        high_level_overview_table(df=ttest_results, alpha=alpha)
    
    with by_protocol:
        by_protocol_table(df=tvl_ttest_results, alpha=alpha)

    with north_star:
        display_north_star_metrics(df1=north_star_metrics, df2=tvl_north_star_metrics, alpha=alpha)

    st.divider()

    # display the 2 metric-specific impact scatterplots
    display_scatterplots(df=simplified_project_table, tvl_df=tvl_north_star_metrics, alpha=alpha)

    st.divider()

    # display a bar chart of measured change by metric
    display_stacked_bar_chart(df=simplified_project_table) 
