import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

def visualize_network(nodes_dict, edges_list):
    """
    Visualizes a supply chain network using NetworkX and matplotlib in Streamlit.
    
    Parameters:
    - nodes_dict: dict of node_code -> Node object
    - edges_list: list of Edge objects
    """

    G = nx.DiGraph()

    # Track node colors separately to ensure they're always available
    node_colors_map = {}

    # Add nodes with attributes
    for code, node in nodes_dict.items():
        node_type = node.type.lower()
        color = (
            'lightblue' if node_type == 'dc' else
            'lightgreen' if node_type == 'wh' else
            'salmon' if node_type == 'store' else
            'gray'
        )
        G.add_node(code, label=node.name)
        node_colors_map[code] = color

    # Add edges (ensure nodes exist)
    for edge in edges_list:
        if edge.source not in G:
            G.add_node(edge.source)
            node_colors_map[edge.source] = 'gray'
        if edge.target not in G:
            G.add_node(edge.target)
            node_colors_map[edge.target] = 'gray'

        G.add_edge(edge.source, edge.target, lead_time=edge.lead_time)

    # Extract node colors
    node_colors = [node_colors_map.get(n, 'gray') for n in G.nodes()]

    # Layout
    pos = nx.spring_layout(G, seed=42)

    # Plot
    fig, ax = plt.subplots(figsize=(12, 8))
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1000, ax=ax)
    nx.draw_networkx_labels(G, pos, labels={n: n for n in G.nodes()}, font_size=10, ax=ax)
    nx.draw_networkx_edges(G, pos, arrowstyle='-|>', arrowsize=20, edge_color='black', ax=ax)

    # Edge labels (lead time)
    edge_labels = {(u, v): f"{d['lead_time']}d" for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9, ax=ax)

    ax.set_title("Supply Chain Network", fontsize=14)
    ax.axis('off')
    st.pyplot(fig)
