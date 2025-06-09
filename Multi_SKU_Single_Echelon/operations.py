from stockpyl.eoq import economic_order_quantity
from math import floor,sqrt

class operations:
    @staticmethod

    def EOQ(ordering_cost,holding_cost,demand):
        eoq,cost=economic_order_quantity(ordering_cost,holding_cost,demand)
        return eoq,cost
    @staticmethod
    def eoq_manual(ordering_cost,holding_cost,demand):
        eoq=sqrt(2*(demand*ordering_cost)/holding_cost)
        return eoq
    @staticmethod
    def cycle_time(eoq,demand):
        return eoq/demand
    @staticmethod

    def cycle_time_in_hr(cycle_time):
        return cycle_time*24
    @staticmethod

    def full_cycle_in_lead_time(lead_time,cycle_time):
        return floor(lead_time/cycle_time)
    @staticmethod

    def effective_lead_time(lead_time,full_cycle_in_lead_time,cycle_time):
        return lead_time-(full_cycle_in_lead_time*cycle_time)
    @staticmethod

    def reorder_point(demand,effective_lead_time):
        return demand*effective_lead_time