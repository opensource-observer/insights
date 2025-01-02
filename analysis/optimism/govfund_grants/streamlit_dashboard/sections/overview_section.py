from typing import Dict, List, Union
import streamlit as st
import pandas as pd

from utils import safe_execution

# streamlit function to display a table of project details and project's link
def display_project_details(project: Dict[str, Union[str, List[str], Dict[str, Union[str, int]]]]) -> None:
    # prepare table rows excluding the proposal link
    rows = [
        ("Project Name", str(project.get("project_name", "N/A"))),
        ("Round", str(project.get("round", "N/A"))),
        ("Cycle", str(project.get("cycle", "N/A"))),
        ("Status", str(project.get("status", "N/A"))),
        ("Amount", str(project.get("amount", "N/A"))),
    ]
    df = pd.DataFrame(rows, columns=["Field", "Value"])

    # style the table (hide index and column headers)
    df_style = (
        df.style.hide(axis='index').set_table_styles([
            {"selector": "th", "props": [("display", "none")]}
        ])
    )

    st.table(df_style)

    # display the proposal link as a clickable hyperlink
    proposal_link = project.get("proposal_link", "N/A")
    if proposal_link != "N/A" and proposal_link != "#":
        st.markdown(f"**Proposal Link:** [View Proposal]({proposal_link})")

# streamlit function to display a dataframe of the projects addresses, along with general info on each
def display_addresses_table(addresses: List[Dict[str, Dict[str, Union[str, List[str]]]]]) -> None:
    address_data = []
    for address in addresses:
        for addr, details in address.items():
            address_data.append({
                "Address": str(addr),
                "Networks": ", ".join(details.get("networks", [])),
                "Tags": ", ".join(details.get("tags", [])),
                "Name": str(details.get("name", "N/A")),
                "Count of Transactions": str(details.get("count_txns", "N/A")),
            })

    df = pd.DataFrame(address_data)

    st.subheader("Addresses")
    st.dataframe(
        df.assign(hack='').set_index('hack'),
        column_config={
            "hack": None,
            "Address": st.column_config.TextColumn(width="large"),
            "Networks": st.column_config.TextColumn(width="small"),
            "Name": st.column_config.TextColumn(width="small")
        }
    )

def overview_section(project):

    st.header("Project Specifics / Overview")
    safe_execution(display_project_details, project)

    # addresses table
    addresses = project.get("addresses", [])
    if addresses:
        safe_execution(display_addresses_table, addresses)

