import pandas as pd
import networkx as nx

# Calculates importance-based centrality measures, PageRank and Eigenvector Centrality.
# Higher PageRank and Eigenvector Centrality scores mean a node is more important and influential in the network due to its connections to other important nodes.

def calculate_importance_centrality(df, level='project'):
    if level not in ['project', 'repo']:
        raise ValueError("Level must be 'project' or 'repo'")

    # Define the nodes based on the level
    nodes = df[level].unique().tolist()
    edges = []

    # Iterate through users to build edges between projects or repos
    for fromId, group in df.groupby('user'):
        entity_set = group[level].unique().tolist()
        entity_set.sort(key=lambda x: group[group[level] == x]['month'].min())
        
        for i in range(len(entity_set) - 1):
            entity1 = entity_set[i]
            entity2 = entity_set[i + 1]
            contributions1 = group[group[level] == entity1]['total_amount'].sum()
            contributions2 = group[group[level] == entity2]['total_amount'].sum()
            harmonic_mean = 2 * contributions1 * contributions2 / (contributions1 + contributions2) if contributions1 + contributions2 > 0 else 0
            edges.append((entity1, entity2, harmonic_mean))

    # Create a directed graph and add nodes and edges
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_weighted_edges_from(edges)

    # Calculate importance-based centrality measures
    page_rank = nx.pagerank(G)
    eigenvector_centrality = nx.eigenvector_centrality(G)

    # Combine results into a DataFrame
    results = pd.Series(page_rank).sort_values(ascending=False)
    results = pd.DataFrame(results, columns=['page_rank'])
    results['eigenvector_centrality'] = pd.Series(eigenvector_centrality)

    return results

# Calculates structural-based centrality measures, Betweenness Centrality and Closeness Centrality.
# Higher Betweenness Centrality scores mean a node plays a crucial role as a bridge between different network parts.
# Higher Closeness Centrality scores mean a node can efficiently communicate with other nodes in the network.

def calculate_structural_centrality(df, level='project'):
    if level not in ['project', 'repo']:
        raise ValueError("Level must be 'project' or 'repo'")

    # Define the nodes based on the level
    nodes = df[level].unique().tolist()
    edges = []

    # Iterate through users to build edges between projects or repos
    for fromId, group in df.groupby('user'):
        entity_set = group[level].unique().tolist()
        entity_set.sort(key=lambda x: group[group[level] == x]['month'].min())
        
        for i in range(len(entity_set) - 1):
            entity1 = entity_set[i]
            entity2 = entity_set[i + 1]
            contributions1 = group[group[level] == entity1]['total_amount'].sum()
            contributions2 = group[group[level] == entity2]['total_amount'].sum()
            harmonic_mean = 2 * contributions1 * contributions2 / (contributions1 + contributions2) if contributions1 + contributions2 > 0 else 0
            edges.append((entity1, entity2, harmonic_mean))

    # Create an undirected graph and add nodes and edges
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_weighted_edges_from(edges)

    # Calculate structural-based centrality measures
    betweenness_centrality = nx.betweenness_centrality(G)
    closeness_centrality = nx.closeness_centrality(G)

    # Combine results into a DataFrame
    results = pd.Series(betweenness_centrality).sort_values(ascending=False)
    results = pd.DataFrame(results, columns=['betweenness_centrality'])
    results['closeness_centrality'] = pd.Series(closeness_centrality)

    return results

# # Usage Example
# df = pd.read_csv("../../github_graph.csv")
# importance_centrality_project = calculate_importance_centrality(df, level='project')
# importance_centrality_repo = calculate_importance_centrality(df, level='repo')

# structural_centrality_project = calculate_structural_centrality(df, level='project')
# structural_centrality_repo = calculate_structural_centrality(df, level='repo')

# print("Importance Centrality for Projects:")
# print(importance_centrality_project)

# print("Importance Centrality for Repos:")
# print(importance_centrality_repo)

# print("Structural Centrality for Projects:")
# print(structural_centrality_project)

# print("Structural Centrality for Repos:")
# print(structural_centrality_repo)
