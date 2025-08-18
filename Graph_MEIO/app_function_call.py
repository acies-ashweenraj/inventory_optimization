import pandas as pd
from config import input_path,extracted_data_path,aggregated_data_path
from data_processing.input import extract_load
from network_builder import build_network
from demand_aggregation.aggregation import aggregate_hierarchy_demand


def data_processing_func():

    extract_load(input_path)

def data_aggregation_func():

    network_df = pd.read_excel(f"{extracted_data_path}/Network_Master.xlsx")
    demand_df = pd.read_excel(f"{extracted_data_path}/Forecasted_Data.xlsx")

    aggregate_hierarchy_demand(network_df,demand_df)


def network_builder_func():

    network_df = pd.read_excel(f"{extracted_data_path}/Network_Master.xlsx")
    cost_df = pd.read_excel(f"{extracted_data_path}/Cost_Parameters.xlsx")
    lead_df = pd.read_excel(f"{extracted_data_path}/Lead_Time.xlsx")
    demand_df = pd.read_excel(f"{aggregated_data_path}/Aggregated_Data.xlsx")

    # print("Demand columns:", demand_df.columns.tolist())


    nodes, edges = build_network(network_df,cost_df,lead_df,demand_df)

    network = {
        "nodes": nodes,  # Dictionary: {node_code: Node}
        "edges": edges   # List: [Edge, Edge, ...]
    }

    # print(f"Network created with {len(network['nodes'])} nodes and {len(network['edges'])} edges")

    # # Sample usage
    # for node_code, node_obj in network["nodes"].items():
    #     print(f"Node: {node_obj.name} | Type: {node_obj.type}")
    #     for metric in node_obj.metrics:
    #         print(f"   SKU: {metric.sku_id} | EOQ: {metric.eoq:.2f} | SS: {metric.safety_stock:.2f}")
    
    return network