import streamlit as st
import pandas as pd
from ..config import DATA_PATHS
from ..utils.visualization import create_sankey_diagram
from ..utils.data_processing import load_data

def render_network_analysis():
    """Render the dependency network analysis tab content."""
    st.header("Dependency Network Analysis")
    st.markdown("""
    ### Stylus SDK Dependency Flow
    This visualization maps the relationship between Stylus SDK users and their external dependencies. The Sankey diagram shows how package owners (on the left) are connected to repositories that use their packages (on the right). This helps us understand which external packages are most commonly used alongside the Stylus SDK and identify key package maintainers in the ecosystem. 
    """)

    # Load dependency data
    dependency_df = load_data(DATA_PATHS["sdk_dependencies"])
    
    # Filter out internal dependencies (where package owner is same as seed repo owner)
    dependency_df = dependency_df[dependency_df['package_repo_owner'] != dependency_df['seed_repo_owner']]
    
    # Add filter for number of top package owners
    top_n = st.slider(
        "Number of Top Package Owners to Show",
        min_value=10,
        max_value=200,
        value=100,
        step=10,
        help="Show the top N package owners based on number of downstream dependencies"
    )
    
    # Create and display the Sankey diagram
    fig = create_sankey_diagram(dependency_df, top_n)
    st.plotly_chart(fig, use_container_width=True)
    
    # Show summary statistics
    st.markdown("### Flow Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Package Sources", len(dependency_df['package_source'].unique()))
    with col2:
        st.metric("Top Package Owners", top_n)
    with col3:
        st.metric("Dependent Repositories", len(dependency_df['seed_repo_owner'].unique())) 