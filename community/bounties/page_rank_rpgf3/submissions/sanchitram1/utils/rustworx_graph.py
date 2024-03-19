import pandas as pd
import rustworkx as rx


class Node:
    """wrapper for a node in a rustworkx graph"""

    def __init__(self, id, metadata) -> None:
        self.index = None
        self.id = id
        self.metadata = metadata

    def __repr__(self) -> str:
        return f"{self.id} @ {self.index}"


class Edge:
    """wrapper for an edge in a rustworkx graph"""

    def __init__(self, source, target, metadata) -> None:
        self.index = None
        self.source = source  # id of Node
        self.target = target
        self.metadata = metadata

    def __repr__(self) -> str:
        return f"{self.source} -> {self.target} @ {self.index}"


class RawGraph(rx.PyDiGraph):
    """wrapper for the raw data structure for the RPGF3 dataset"""

    def __init__(self) -> None:
        super().__init__()
        self.index_map = {}
        self.node_labels = ["user", "repo", "project"]
        self.edge_labels = ["provides", "contributes"]
        self.contribute_types = ["PR", "Issue", "Commit"]

    def add_project_provides(self, provides: pd.DataFrame):
        """assume provides is pandas dataframe

        at a minimum, it must have:
        - project
        - repo
        - total_amount
        """
        necessary = ["project", "repo"]

        if not all([n in provides.columns for n in necessary]):
            raise ValueError(f"{provides.columns} != {necessary}")

        provides = [
            (
                self.index_map[provide.project],
                self.index_map[provide.repo],
                Edge(
                    self.index_map[provide.project],
                    self.index_map[provide.repo],
                    {
                        "label": "provides",
                    },
                ),
            )
            for provide in provides.itertuples()
        ]

        indices = self.add_edges_from(provides)

        for index, data in self.edge_index_map().items():
            data[2].index = index

    def add_user_contributions(self, contributions: pd.DataFrame):
        """assume contributions is pandas dataframe

        at a minimum, it must have:
        - user
        - repo
        - type
        - total_amount
        """
        necessary = ["user", "repo", "type", "total_amount"]

        if not all([n in contributions.columns for n in necessary]):
            raise ValueError(f"{contributions.columns} != {necessary}")

        contributions = [
            (
                self.index_map[contribution.user],
                self.index_map[contribution.repo],
                Edge(
                    self.index_map[contribution.user],
                    self.index_map[contribution.repo],
                    {
                        "type": contribution.type,
                        "month": contribution.month,
                        "total_amount": contribution.total_amount,
                        "label": "contributes",
                    },
                ),
            )
            for contribution in contributions.itertuples()
        ]

        indices = self.add_edges_from(contributions)

        for index, data in self.edge_index_map().items():
            data[2].index = index

    def update_node_indices(self):
        """update the index of each node in the graph"""
        for i, node in enumerate(self.nodes()):
            node.index = i
    
    def update_edge_indices(self):
        """update the index of each edge in the graph"""
        for i, edge in enumerate(self.edges()):
            edge.index = i

    def load_nodes(self, nodes: pd.DataFrame, node_label: str):
        """assume nodes is pandas dataframe"""
        necessary = [node_label]

        if not all([n in nodes.columns for n in necessary]):
            raise ValueError(f"{nodes.columns} != {necessary}")

        nodes = [Node(id, {"label": node_label}) for id in nodes[node_label].values]
        node_ids = [node.id for node in nodes]
        indices = self.add_nodes_from(nodes)
        self.index_map.update({id: index for id, index in zip(node_ids, indices)})

    def add_projects(self, projects: pd.DataFrame):
        """assume projects is pandas dataframe

        projects might have some metadata, but at a minimum, it must have:
        - id
        """
        self.load_nodes(projects, "project")

        # Update the created Node objects with the metadata
        for node in projects.to_dict(orient="records"):
            self[self.index_map[node["project"]]].metadata.update(node)


class UserGraph(rx.PyDiGraph):
    """wrapper for a user to user graph for the RPGF3 distributions"""
