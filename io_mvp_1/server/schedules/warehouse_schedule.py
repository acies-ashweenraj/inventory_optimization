import pandas as pd
from math import floor
from datetime import datetime, timedelta
from server.Preassumptions import WAREHOUSE_SCHEDULE  
from server.schedules import common_schedule


def warehouses_schedule(df):
    common_schedule.common_schedule_func(df,"Warehouse")
   