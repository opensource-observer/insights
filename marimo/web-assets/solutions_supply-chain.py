import marimo

__generated_with = "0.17.5"
app = marimo.App(width="full")


@app.cell
def title_markdown(mo):
    mo.md(r"""
    # How efficient is our supply chain?
    """)
    return


@app.cell
def analysis_settings(commodity_list, mo, supplier_list):
    supplier_filter = mo.ui.dropdown(
        options=["All Suppliers"] + supplier_list,
        value="All Suppliers",
        label="Supplier:"
    )
    commodity_filter = mo.ui.dropdown(
        options=["All Commodities"] + commodity_list,
        value="All Commodities",
        label="Commodity:"
    )
    time_period = mo.ui.dropdown(
        options=["Last Month", "Last Quarter", "Last 6 Months"],
        value="Last Month",
        label="Time Period:"
    )
    mo.vstack([
        mo.md("### Analysis Settings:"),
        mo.hstack([supplier_filter, commodity_filter, time_period], widths="equal", gap=2)
    ])
    return commodity_filter, supplier_filter


@app.cell
def analysis_results(commodity_filter, df, make_sankey, mo, supplier_filter):
    # Filter data based on selections
    filtered_df = df.copy()
    if supplier_filter.value != "All Suppliers":
        filtered_df = filtered_df[filtered_df['supplier_id'] == supplier_filter.value]
    if commodity_filter.value != "All Commodities":
        filtered_df = filtered_df[filtered_df['commodity'] == commodity_filter.value]

    # Calculate stats
    # Stat 1: Average lead time (weighted by quantity)
    total_qty = filtered_df['qty'].sum()
    weighted_lead_time = (filtered_df['qty'] * filtered_df['lead_time_days']).sum() / total_qty if total_qty > 0 else 0

    # Stat 2: On-time delivery percentage
    total_deliveries = len(filtered_df)
    on_time_deliveries = len(filtered_df[filtered_df['status'] == 'on_time'])
    on_time_pct = (on_time_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0

    # Stat 3: Cost variance vs contract (baseline cost per commodity)
    baseline_costs = {'Cocoa': 2800, 'Coffee': 3200, 'Sugar': 1500}
    avg_actual_cost = filtered_df['cost_usd'].mean()
    # Calculate weighted baseline based on commodities in filtered data
    commodity_counts = filtered_df['commodity'].value_counts()
    weighted_baseline = sum(baseline_costs[c] * count for c, count in commodity_counts.items()) / len(filtered_df)
    cost_variance = avg_actual_cost - weighted_baseline

    # Stat 4: Inventory coverage days (simulated based on qty and lead time)
    avg_daily_usage = 50  # units per day (simulated)
    total_inventory = filtered_df['qty'].sum()
    coverage_days = total_inventory / avg_daily_usage if avg_daily_usage > 0 else 0

    # Generate the Sankey figure
    _fig = make_sankey(filtered_df)

    # Create stats widgets
    stat1 = mo.stat(
        label="Avg Lead Time", 
        bordered=True, 
        value=f"{weighted_lead_time:.1f} days",
        caption="Weighted by quantity"
    )
    stat2 = mo.stat(
        label="On-Time Delivery", 
        bordered=True, 
        value=f"{on_time_pct:.0f}%",
        caption=f"{on_time_deliveries} of {total_deliveries} orders"
    )
    stat3 = mo.stat(
        label="Cost Variance", 
        bordered=True, 
        value=f"${cost_variance:+,.0f}",
        caption="vs contract baseline"
    )
    stat4 = mo.stat(
        label="Inventory Coverage", 
        bordered=True, 
        value=f"{coverage_days:.0f} days",
        caption=f"{total_inventory:,.0f} units on hand"
    )

    # Generate the results dashboard
    mo.vstack([
        mo.md("### Supply Chain Metrics:"),
        mo.hstack([stat1, stat2, stat3, stat4], widths="equal", gap=1),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return


@app.cell
def make_sankey(go):
    # Color scheme
    COLOR_SUPPLIER = '#253494'    # Dark blue
    COLOR_PROCESSOR = '#41B6C4'   # Teal
    COLOR_DC = '#A1DAB4'          # Light green

    def make_sankey(df):
        # Build Sankey diagram: Supplier → Processor → Distribution Center
        # For this simplified version, we'll create synthetic processor and DC nodes

        # Create node labels
        suppliers = sorted(df['supplier_id'].unique())
        processors = ['Processor A', 'Processor B']
        distribution_centers = ['DC East', 'DC West', 'DC Central']

        node_labels = suppliers + processors + distribution_centers

        # Assign indices
        supplier_indices = {s: i for i, s in enumerate(suppliers)}
        processor_indices = {p: len(suppliers) + i for i, p in enumerate(processors)}
        dc_indices = {d: len(suppliers) + len(processors) + i for i, d in enumerate(distribution_centers)}

        # Build flows
        sources = []
        targets = []
        values = []
        colors = []

        # Supplier → Processor flows
        # Distribute quantities from each supplier to processors
        for supplier in suppliers:
            supplier_df = df[df['supplier_id'] == supplier]
            total_qty = supplier_df['qty'].sum()

            # Split between processors (60/40)
            for i, processor in enumerate(processors):
                qty = total_qty * (0.6 if i == 0 else 0.4)
                sources.append(supplier_indices[supplier])
                targets.append(processor_indices[processor])
                values.append(qty)
                colors.append('rgba(37, 52, 148, 0.4)')  # Blue with transparency

        # Processor → DC flows
        # Calculate total at each processor and distribute to DCs
        for processor in processors:
            processor_idx = processor_indices[processor]
            # Sum all incoming flows to this processor
            processor_total = sum(values[i] for i, t in enumerate(targets) if t == processor_idx)

            # Distribute to DCs (40/35/25 split)
            distribution = [0.4, 0.35, 0.25]
            for i, dc in enumerate(distribution_centers):
                qty = processor_total * distribution[i]
                sources.append(processor_idx)
                targets.append(dc_indices[dc])
                values.append(qty)
                colors.append('rgba(65, 182, 196, 0.4)')  # Teal with transparency

        # Create node colors
        node_colors = (
            [COLOR_SUPPLIER] * len(suppliers) +
            [COLOR_PROCESSOR] * len(processors) +
            [COLOR_DC] * len(distribution_centers)
        )

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="white", width=0.5),
                label=node_labels,
                color=node_colors
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=colors
            )
        )])

        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="white",
            font=dict(size=12, color="#111"),
            margin=dict(l=20, r=20, t=40, b=20),
            title=dict(
                text="Supply Chain Flow: Suppliers → Processors → Distribution Centers",
                x=0.5,
                xanchor='center',
                font=dict(size=14)
            )
        )

        return fig
    return (make_sankey,)


@app.cell
def get_data(pd):
    # Create dummy supply chain data
    # 24 rows across 4 suppliers, 3 commodities

    dates = pd.date_range(start='2024-11-01', periods=24, freq='D')

    suppliers = ['Supplier A', 'Supplier B', 'Supplier C', 'Supplier D']
    commodities = ['Cocoa', 'Coffee', 'Sugar']
    statuses = ['on_time', 'delayed', 'early']

    data = []
    lot_id = 1000

    # Generate 24 rows with variation
    for i, date in enumerate(dates):
        supplier = suppliers[i % 4]
        commodity = commodities[i % 3]

        # Vary quantities
        if supplier == 'Supplier A':
            qty = 800 + (i * 25)
        elif supplier == 'Supplier B':
            qty = 1000 + (i * 30)
        elif supplier == 'Supplier C':
            qty = 600 + (i * 20)
        else:
            qty = 900 + (i * 28)

        # Vary lead times
        if supplier in ['Supplier A', 'Supplier B']:
            lead_time = 7 + (i % 5)
        else:
            lead_time = 10 + (i % 7)

        # Vary costs by commodity with significant variance
        base_costs = {'Cocoa': 2800, 'Coffee': 3200, 'Sugar': 1500}
        # Add supplier-specific markup/discount and time-based variation
        supplier_variance = {'Supplier A': 150, 'Supplier B': -100, 'Supplier C': 200, 'Supplier D': -50}
        time_variance = ((i % 8) * 80) - 200  # More variation over time
        cost = base_costs[commodity] + supplier_variance[supplier] + time_variance

        # Vary status (mostly on_time)
        if i % 7 == 0:
            status = 'delayed'
        elif i % 11 == 0:
            status = 'early'
        else:
            status = 'on_time'

        data.append({
            'date': date,
            'supplier_id': supplier,
            'lot_id': f'LOT-{lot_id + i}',
            'commodity': commodity,
            'qty': qty,
            'lead_time_days': lead_time,
            'cost_usd': cost,
            'status': status
        })

    df = pd.DataFrame(data)
    supplier_list = sorted(df['supplier_id'].unique().tolist())
    commodity_list = sorted(df['commodity'].unique().tolist())

    return commodity_list, df, supplier_list


@app.cell
def import_libraries():
    import pandas as pd
    import plotly.graph_objects as go
    return go, pd


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return (mo,)


if __name__ == "__main__":
    app.run()
