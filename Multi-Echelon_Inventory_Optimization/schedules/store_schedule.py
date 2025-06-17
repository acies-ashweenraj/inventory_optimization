import pandas as pd
from math import floor
from datetime import datetime, timedelta
from Preassumptions import STORE_SCHEDULE  
# from common_schedule import common_schedule
from schedules import common_schedule

def stores_schedule(df):
    common_schedule.common_schedule_func(df,"Store")