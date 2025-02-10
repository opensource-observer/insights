import pandas as pd

from utils import (read_in_stored_dfs_for_projects,
                   read_in_defi_llama_protocols, 
                   return_protocol, 
                   read_in_grants)

from config import (GRANTS_PATH, 
                    DEFI_LLAMA_PROTOCOLS_PATH,
                    STORED_DATA_PATH)

from sections.statistical_analysis_section import (aggregate_datasets, 
                                                   concat_aggregate_with_forecasted, 
                                                   split_dataset_by_date,
                                                   aggregate_split_datasets_by_metrics,
                                                   determine_statistics)

#                                                                                       header representing each metric
# for each project, Project Name, round, cycle, status, amount, date range | statistics repeat for each metric

data = {
    "Project Name" : [],
    "Round" : [],
    "Cycle" : [],
    "Grant Status" : [],
    "Grant Amount" : [],
    "Grant Recieved (to date)?": [],
    "Date Funds Recieved": [],
    "Balance Left (to date)": [],
    "Date Range" : [],
    "Transaction Count" : [], 
    "Active Users" : [], 
    "Unique Users" : [], 
    "Total Transferred" : [], 
    "Net Transferred" : [],
    "TVL" : [],
    "Retained Daily Active Users": [],
    "DAA/MAA" : [],
    "Transaction Count (forecasted)" : [], 
    "Active Users (forecasted)" : [], 
    "Unique Users (forecasted)" : [], 
    "Total Transferred (forecasted)" : [], 
    "Net Transferred (forecasted)" : [],
    "TVL (forecasted)" : [],
    "Retained Daily Active Users (forecasted)": [],
    "DAA/MAA (forecasted)" : []
}

projects = read_in_grants(grants_path=GRANTS_PATH)
defi_llama_protocols = read_in_defi_llama_protocols(path=DEFI_LLAMA_PROTOCOLS_PATH)

header = [
    ('General Info', "Project Name"),
    ('General Info', "Round"),
    ('General Info', "Cycle"),
    ('General Info', "Grant Status"),
    ('General Info', "Grant Amount"),
    ("General Info", "Grant Recieved (to date)?"),
    ("General Info", "Date Funds Recieved"),
    ("General Info", "Balance Left (to date)"),
    ('General Info', "Date Range")
]

# define metric groups
metric_list = ["Transaction Count", "Active Users", "Unique Users", "Total Transferred", "Net Transferred", "TVL", "Retained Daily Active Users", "DAA/MAA"]

# unified loop for both metric groups
for metric in metric_list:
    # add the base metric columns
    header.extend([
        (metric, "Percent Change"),
        (metric, "Test Statistic"),
        (metric, "P Value"),
        (metric, "P Value Formatted"),
    ])
    # add forecasted 
    forecasted_metric = f"{metric} (forecasted)"
    header.extend([
        (forecasted_metric, "Percent Change"),
        (forecasted_metric, "Test Statistic"),
        (forecasted_metric, "P Value"),
        (forecasted_metric, "P Value Formatted"),
    ])

for project_name, project in projects.items():
    print(f"starting project: {project_name}")

    project_results = {}
    clean_name = project_name.lower().replace(" ", "_").replace(".", "-").replace("/","-")

    data["Project Name"].append(str(project.get("project_name", "N/A")))
    data["Round"].append(str(project.get("round", "N/A")))
    data["Cycle"].append(str(project.get("cycle", "N/A")))
    data["Grant Status"].append(str(project.get("status", "N/A")))
    data["Grant Amount"].append(str(project.get("amount", "N/A")))
    data["Grant Recieved (to date)?"].append(str(project.get("recieved_todate", "N/A")))
    data["Date Funds Recieved"].append(str(project.get("funds_recieved_date", "N/A")))
    data["Balance Left (to date)"].append(str(project.get("balance_left", "N/A")))

    project_protocol = return_protocol(defi_llama_protocols=defi_llama_protocols, project=project_name)
    grant_date = project['funds_recieved_date']

    project_datasets = read_in_stored_dfs_for_projects(
        project_name=project_name,
        data_path=STORED_DATA_PATH,
        protocol=project_protocol
    )
    project_daily_transactions_df = project_datasets['daily_transactions']
    project_net_transaction_flow_df = project_datasets['net_transaction_flow']
    project_chain_tvls_df = project_datasets['chain_tvls']
    project_tokens_in_usd_df = project_datasets['tokens_in_usd']
    project_tvl_df = project_datasets['tvl']
    project_forecasted_df = project_datasets['forecasted']

    if project_forecasted_df is not None:
        if "forecasted_TVL" in project_forecasted_df.columns:
            project_forecasted_df.drop("forecasted_TVL", axis=1, inplace=True)
            project_forecasted_df.rename(columns={"forecasted_TVL_opchain":"forecasted_TVL"}, inplace=True)

    if project_daily_transactions_df is not None and not project_daily_transactions_df.empty:
        project_daily_transactions_df['transaction_date'] = pd.to_datetime(
            project_daily_transactions_df['transaction_date'], errors='coerce'
        )

    if project_net_transaction_flow_df is not None and not project_net_transaction_flow_df.empty:
        project_net_transaction_flow_df['transaction_date'] = pd.to_datetime(
            project_net_transaction_flow_df['transaction_date'], errors='coerce'
        )

    if project_chain_tvls_df is not None and not project_chain_tvls_df.empty:
        project_chain_tvls_df['readable_date'] = pd.to_datetime(
            project_chain_tvls_df['readable_date'].str.strip(), errors='coerce'
        )

    if project_tokens_in_usd_df is not None and not project_tokens_in_usd_df.empty:
        project_tokens_in_usd_df['readable_date'] = pd.to_datetime(
            project_tokens_in_usd_df['readable_date'].str.strip(), errors='coerce'
        )

    if project_tvl_df is not None and not project_tvl_df.empty:
        project_tvl_df['readable_date'] = pd.to_datetime(
            project_tvl_df['readable_date'].str.strip(), errors='coerce'
        )

    if project_forecasted_df is not None and not project_forecasted_df.empty:
        project_forecasted_df['date'] = pd.to_datetime(
            project_forecasted_df['date'], errors='coerce'
        )

    min_date = project_daily_transactions_df['transaction_date'].min()
    max_date = project_daily_transactions_df['transaction_date'].max()

    data['Date Range'].append(f"{min_date.date()} - {max_date.date()}")

    aggregated_dataset = aggregate_datasets(
        daily_transactions_df=project_daily_transactions_df,
        net_transaction_flow_df=project_net_transaction_flow_df,
        tvl_df=project_tvl_df,
        grant_date=grant_date
    )

    if project_forecasted_df is not None:
        combined_df = concat_aggregate_with_forecasted(aggregated_dataset, project_forecasted_df)
    else:
        combined_df = aggregated_dataset

    pre_grant_df, post_grant_df = split_dataset_by_date(combined_df, grant_date=grant_date)
    post_grant_df = post_grant_df[post_grant_df["grant_label"] == "post grant"]
    curr_forecasted_df = combined_df[combined_df["grant_label"] == "forecast"]

    for metric in metric_list:
        if metric in combined_df.columns:
            # handle both pre-grant data and forecasted data (if applicable)
            metric_mapping = {
                metric: pre_grant_df,
                f"{metric} (forecasted)" : curr_forecasted_df
            }

            sample_2 = post_grant_df[["date", metric, "grant_label"]]

            for curr_metric, sample_1 in metric_mapping.items():
                sample_1 = sample_1[["date", metric, "grant_label"]]

                # calculate and aggregate metrics for pre-grant and post-grant data
                aggregated_metrics = aggregate_split_datasets_by_metrics([(sample_1, sample_2)], [metric])
                metric_table = determine_statistics(aggregated_metrics[0][0], aggregated_metrics[0][1])

                # store calculated metrics
                data[curr_metric].append({
                    "Percent Change": metric_table['percent_change'].iloc[0],
                    "Test Statistic": metric_table['test_statistic'].iloc[0],
                    "P Value": metric_table['p_value'].iloc[0],
                    "P Value Formatted": metric_table['p_value_formatted'].iloc[0]
                })

        else:
            # handle cases where the metric is missing in the dataset
            data[metric].append({
                "Percent Change": "N/A",
                "Test Statistic": "N/A",
                "P Value": "N/A",
                "P Value Formatted": "N/A"
            })

            # add N/A for forecasted data
            data[f"{metric} (forecasted)"].append({
                "Percent Change": "N/A",
                "Test Statistic": "N/A",
                "P Value": "N/A",
                "P Value Formatted": "N/A"
            })
        
    print(f"project done")

# create multi-index for the columns
multi_index = pd.MultiIndex.from_tuples(header)

# prepare flattened data to match multi-index structure
flat_data = []
for i in range(len(data["Project Name"])): 
    row = {
        ("General Info", "Project Name"): data["Project Name"][i],
        ("General Info", "Round"): data["Round"][i],
        ("General Info", "Cycle"): data["Cycle"][i],
        ("General Info", "Grant Status"): data["Grant Status"][i],
        ("General Info", "Grant Amount"): data["Grant Amount"][i],
        ("General Info", "Grant Recieved (to date)?"): data["Grant Recieved (to date)?"][i],
        ("General Info", "Date Funds Recieved"): data["Date Funds Recieved"][i],
        ("General Info", "Balance Left (to date)"): data["Balance Left (to date)"][i],
        ("General Info", "Date Range"): data["Date Range"][i]
    }

    # iterate over all metrics (including forecasted ones)
    for metric in metric_list:
        # check if the metric has a forecasted counterpart
        metric_variants = [metric, f"{metric} (forecasted)"]

        for curr_metric in metric_variants:
            # retrieve metric data or use an empty dictionary if out of bounds
            metric_data = data[curr_metric][i] if i < len(data[curr_metric]) else {}

            # populate the row with the relevant data
            row[(curr_metric, "Percent Change")] = metric_data.get("Percent Change", "N/A")
            row[(curr_metric, "Test Statistic")] = metric_data.get("Test Statistic", "N/A")
            row[(curr_metric, "P Value")] = metric_data.get("P Value", "N/A")
            row[(curr_metric, "P Value Formatted")] = metric_data.get("P Value Formatted", "N/A")

    # append the populated row to the flat_data list
    flat_data.append(row)


# convert flattened data into a dataframe with multi-index columns
output_df = pd.DataFrame(flat_data, columns=multi_index)

# save to csv
output_path = f"{STORED_DATA_PATH}ttest_results2.csv"
output_df.to_csv(output_path, index=False)
