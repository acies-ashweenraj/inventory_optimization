

class Node:
    def __init__(self,code : str,name : str,type : str,holding_cost : float,ordering_cost : float,capacity : int,service_level : int,metrics: list,sku_list : list):
        """ This class consists of all the parameters required to define an echelon"""
        self.code = code
        self.name = name
        self.type = type
        self.holding_cost = holding_cost
        self.ordering_cost = ordering_cost
        self.capacity = capacity
        self.service_level = service_level
        self.metrics = metrics #list of objects of the sku
        self.sku_list = sku_list

class Edge:
    def __init__(self,source : str,target : str,lead_time : float,reverse_flow: bool):
        """ This class consists of all the parameters required to define an route between echelon"""

        self.source = source
        self.target = target
        self.lead_time = lead_time
        self.reverse_flow = reverse_flow

class Metrics:
    def __init__(self,sku_id : str,demand : int,safety_stock : int,rop : int,inventory_turnover_ratio : float,average_inventory : float,stock_coverage_time : float,eoq : float,std_demand : float):
        """ This class consists of all the calculated metrics of the respective echelon for that respective sku"""

        self.sku_id = sku_id
        self.demand = demand
        self.safety_stock = safety_stock
        self.rop = rop
        self.inventory_turnover_ratio = inventory_turnover_ratio
        self.average_inventory = average_inventory
        self.stock_coverage_time = stock_coverage_time
        self.eoq = eoq
        self.std_demand = std_demand
        
