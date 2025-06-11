
ORDERING_COST = {
    'DC': 200,
    'WH1': 50,
    'WH2': 50,
    'ST1': 10,
    'ST2': 10,
    'ST3': 10
}

HOLDING_COST = {
    'DC': 0.5,
    'WH1': 0.7,
    'WH2': 0.7,
    'ST1': 1.0,
    'ST2': 1.0,
    'ST3': 1.0
}

LEAD_TIME1 = {
    ('DC1', 'WH1'): 3,
    ('DC1', 'WH2'): 4,
    ('WH1', 'ST1'): 2,
    ('WH1', 'ST2'): 3,
    ('WH2', 'ST3'): 2
}

LEAD_TIME = {
    'WH1': 3,
    'WH2': 4,
    'ST1': 2,
    'ST2': 3,
    'ST3': 2,
    'DC': 2
}

CODE_MAP={
    40101:"ST1",
    100868:"ST2",
    1052013:"ST3",
    106406:"WH1",
    106968:"WH2",
    106446:"DC"
}

Z_SCORE = 1.65

STORE_SCHEDULE=[]

WAREHOUSE_SCHEDULE=[]
