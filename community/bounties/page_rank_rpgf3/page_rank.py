"""
simple page rank algorithm
applied to rpgf3 github data

"""


import pandas as pd
import networkx as nx


df = pd.read_csv("github_graph.csv")
nodes = df['project'].unique().tolist()
edges = []

for fromId, group in df.groupby('user'):
    project_set = group['project'].unique().tolist()
    project_set.sort(key=lambda x: group[group['project'] == x]['month'].min())
    
    for i in range(len(project_set) - 1):
        project1 = project_set[i]
        project2 = project_set[i + 1]
        contributions1 = group[group['project'] == project1]['total_amount'].sum()
        contributions2 = group[group['project'] == project2]['total_amount'].sum()
        harmonic_mean = 2 * contributions1 * contributions2 / (contributions1 + contributions2) if contributions1 + contributions2 > 0 else 0
        edges.append((project1, project2, harmonic_mean))

G = nx.DiGraph()
G.add_nodes_from(nodes)
G.add_weighted_edges_from(edges)
page_rank = nx.pagerank(G)

results = pd.Series(page_rank).sort_values(ascending=False)
print(results)
