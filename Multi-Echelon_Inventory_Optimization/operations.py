# from stockpyl.eoq import economic_order_quantity
from math import floor,sqrt
from Preassumptions import ORDERING_COST, HOLDING_COST, LEAD_TIME

class operations:
    def EOQ(ordering_cost,holding_cost,demand):
        eoq,cost=economic_order_quantity(ordering_cost,holding_cost,demand)
        return eoq
    def eoq_manual(ordering_cost,holding_cost,demand):
        eoq=sqrt(2*(demand*ordering_cost)/holding_cost)
        return eoq
    def cycle_time(eoq,demand):
        return eoq/demand
    def cycle_time_month_to_days(cycle_time):
        return cycle_time*30
    def cycle_time_days_to_hrs(cycle_time):
        return cycle_time*24
    def full_cycle_in_lead_time(lead_time,cycle_time):
        return floor(lead_time/cycle_time)
    def effective_lead_time(lead_time,full_cycle_in_lead_time,cycle_time):
        return lead_time-(full_cycle_in_lead_time*cycle_time)
    def reorder_point(demand,effective_lead_time):
        return demand*effective_lead_time
    
    def get_ordering_cost(node):
        return ORDERING_COST[node]

    def get_holding_cost(node):
        return HOLDING_COST[node]

    def get_lead_time(parent, child):
        return LEAD_TIME[(parent, child)]