
# ORDERING_COST = {
#     'DC': 200,
#     'WH1': 50,
#     'WH2': 50,
#     'ST1': 10,
#     'ST2': 10,
#     'ST3': 10
# }

# HOLDING_COST = {
#     'DC': 0.5,
#     'WH1': 0.7,
#     'WH2': 0.7,
#     'ST1': 1.0,
#     'ST2': 1.0,
#     'ST3': 1.0
# }

# LEAD_TIME1 = {
#     ('DC1', 'WH1'): 3,
#     ('DC1', 'WH2'): 4,
#     ('WH1', 'ST1'): 2,
#     ('WH1', 'ST2'): 3,
#     ('WH2', 'ST3'): 2
# }

# LEAD_TIME = {
#     'WH1': 3,
#     'WH2': 4,
#     'ST1': 2,
#     'ST2': 3,
#     'ST3': 2,
#     'DC': 2
# }

# CODE_MAP={
#     40101:"ST1",
#     100868:"ST2",
#     1052013:"ST3",
#     106406:"WH1",
#     106968:"WH2",
#     106446:"DC"
# }

# Z_SCORE = 1.65

# STORE_SCHEDULE=[]

# WAREHOUSE_SCHEDULE=[]


import pandas as pd

# File paths
network_file = r"Multi-Echelon_Inventory_Optimization\data\network_parameter.xlsx"
lead_time_file = r"Multi-Echelon_Inventory_Optimization\data\lead_time.xlsx"

# Read files
costs_df = pd.read_excel(network_file)
lead_df = pd.read_excel(lead_time_file)

# Code to name mapping
CODE_MAP = dict(zip(costs_df["Node Code"], costs_df["Node Name"]))

# Cost dictionaries
ORDERING_COST = dict(zip(costs_df["Node Name"], costs_df["Ordering Cost"]))
HOLDING_COST = dict(zip(costs_df["Node Name"], costs_df["Holding Cost"]))

# Map node codes in lead_df to names using CODE_MAP
lead_df["Source Name"] = lead_df["Source Code"].map(CODE_MAP)
lead_df["Target Name"] = lead_df["Target Code"].map(CODE_MAP)

# Create LEAD_TIME dictionary as {(Source, Target): LeadTime}
LEAD_TIME = dict(zip(zip(lead_df["Source Name"], lead_df["Target Name"]), lead_df["Lead Time"]))

# Add default 0 lead time for self-loops if needed
LEAD_TIME[(CODE_MAP[1040336], CODE_MAP[1040336])] = 0
LEAD_TIME[(CODE_MAP[106701], CODE_MAP[106701])] = 0

# Other constants
Z_SCORE = 1.65
STORE_SCHEDULE = []
WAREHOUSE_SCHEDULE = []


# print(CODE_MAP)
# print("\n")
# print(ORDERING_COST)
# print("\n")
# print(HOLDING_COST)
# print("\n")
# print(LEAD_TIME)