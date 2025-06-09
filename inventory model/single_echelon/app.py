from weekly import weekly_data
import os
from daily import daily_data,daily_to_weekly
from variables import LEAD_TIME,SKU1_HOLDING_COST,SKU1_ORDERING_COST

#weekly eoq
print("Current working directory:", os.getcwd())

forecasted_path="single_echelon/data/Fact.DemandPlan.csv"

final_df=weekly_data(forecasted_path,SKU1_ORDERING_COST,SKU1_HOLDING_COST,LEAD_TIME)
print(final_df.head())

# daily_to_weekly(forecasted_path)
# daily_prepared_data=r"C:\Users\DELL\Desktop\inventory model\single echelon\data\daily_prepared_data.csv"
# daily_final_data=daily_data(daily_prepared_data,SKU1_ORDERING_COST,SKU1_HOLDING_COST,LEAD_TIME)
# print(daily_final_data.head())


