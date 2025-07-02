from data_processing.input import load_file_as_dataframe
from app_function_call import data_processing_func,network_builder_func,data_aggregation_func
import streamlit as st
from entities import Node, Edge  # Your classes
from graph_viz import visualize_network  # function from above
import networkx as nx
import matplotlib.pyplot as plt




# This function will extract the excel file its sheets and then preprocess it and store it in the output/extracted_data
data_processing_func()

data_aggregation_func()

network = network_builder_func()
nodes = network["nodes"]
edges = network["edges"]



network = {
    "nodes": nodes,  # Dictionary: {node_code: Node}
    "edges": edges  # List: [Edge, Edge, ...]
}



# Visualize
visualize_network(nodes, edges)







