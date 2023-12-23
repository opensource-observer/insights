import matplotlib.pyplot as plt
import networkx as nx


def network_graph(nodes, edges, figsize=(10,10), dpi=300, scale=1, k=.1, min_degree=1, styling=None):

    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    G.remove_edges_from(nx.selfloop_edges(G))
    G = nx.k_core(G, min_degree)
    degrees = dict(G.degree)
    pos = nx.spring_layout(G, scale=scale, k=k)

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    nx.draw(G, pos, nodelist=degrees, node_size=[degrees[k]*10 for k in degrees], ax=ax, **styling)
    ax.set_title("Projects with Common Contributors")
    ax.axis('off')

    return fig, ax
