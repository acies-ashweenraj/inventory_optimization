from data_processing.input import load_file_as_dataframe
from app_function_call import data_processing_func,network_builder_func,data_aggregation_func


network = {
    "nodes": {},  # Dictionary: {node_code: Node}
    "edges": []   # List: [Edge, Edge, ...]
}

# This function will extract the excel file its sheets and then preprocess it and store it in the output/extracted_data
data_processing_func()

data_aggregation_func()

network["nodes"],network["edges"] = network_builder_func()





