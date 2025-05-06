import streamlit as st
import pandas as pd
from ..config import DATA_PATHS

def render_overview():
    """Render the overview tab content."""
    st.header("Overview")
    st.markdown("""
    Welcome to the **Stylus Sprint Ecosystem Dashboard**, a data-driven exploration of developer activity, project engagement, and network effects from the [Arbitrum Stylus Sprint](https://blog.arbitrum.io/stylus-sprint/) grant program.

    Launched by the Arbitrum DAO, Stylus Sprint is a 5 million ARB initiative supporting projects building with Stylus — a new WASM-based virtual machine that lets developers write smart contracts in Rust, C, C++, and other WebAssembly-compatible languages.

    This dashboard helps you:
    - 📋 **Overview**: Explore who's building what in the Stylus Sprint and where to dig deeper.
    - 👩‍💻 **Developer Ecosystem Health**: Uncover how developer activity is shaping the future of Stylus and Arbitrum.
    - 📈 **Stylus Sprint Activity Analysis**: Dive into engagement trends and surface signals of momentum across projects.
    - 🔍 **Project Deep Dive**: Zoom in on any project to decode its development velocity and community dynamics.
    - ⚠️ **Risk Assessment**: Spot early warning signs in project health.
    - 🕸️ **Network Analysis**: Trace the growing influence of Stylus through a web of SDK dependencies.
    """)

    st.markdown("""
    This section lists all projects that are part of the Stylus Sprint program analysis.
    """)
    st.caption("To update your project's GitHub repositories, package links (e.g., NPM, Crates), or contract deployments in the OSS Directory, please follow the instructions outlined in [this](https://docs.google.com/document/d/1bOjjHiaY-8bx5d_Bwce4ePDYq3H7W8r_3Wq0dJCyLoA/edit?tab=t.0) document.")
    
    # Read and process project data
    project_orgs = pd.read_csv(DATA_PATHS["project_orgs"])
    project_applications = pd.read_csv(DATA_PATHS["project_applications"])
    
    # Merge the dataframes
    projects_df = pd.merge(
        project_applications,
        project_orgs,
        on='project_name',
        how='left'
    )
    
    # Select and rename columns
    projects_df = projects_df[['questbook_title', 'artifact_namespace', 'questbook_link', 'ossd_link']]
    
    # Add GitHub URL prefix to org
    projects_df['artifact_namespace'] = 'https://github.com/' + projects_df['artifact_namespace']
    
    # Sort by project title
    projects_df = projects_df.sort_values('questbook_title', key=lambda x: x.str.lower())
    
    # Display the table
    st.dataframe(
        projects_df,
        column_config={
            "questbook_title": "Project Title",
            "questbook_link": st.column_config.LinkColumn("Questbook Link", display_text="Open Questbook Application"),
            "artifact_namespace": st.column_config.LinkColumn("GitHub Organization"),
            "ossd_link": st.column_config.LinkColumn("OSS Directory Link", display_text="Open Project YAML File")
        },
        hide_index=True,
        use_container_width=False,
        width=2000,
        height=900
    ) 