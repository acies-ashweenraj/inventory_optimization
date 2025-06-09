
ORDERING_COST = {
    'DC1': 200,
    'WH1': 50,
    'WH2': 50,
    'Store1': 10,
    'Store2': 10,
    'Store3': 10
}

HOLDING_COST = {
    'DC1': 0.5,
    'WH1': 0.7,
    'WH2': 0.7,
    'Store1': 1.0,
    'Store2': 1.0,
    'Store3': 1.0
}

LEAD_TIME = {
    ('DC1', 'WH1'): 3,
    ('DC1', 'WH2'): 4,
    ('WH1', 'Store1'): 2,
    ('WH1', 'Store2'): 3,
    ('WH2', 'Store3'): 2
}
