from pathlib import Path

input_path = r"\data\Multi_Sku.xlsx"
demand_path = r"C:\Users\UserR93\Desktop\inv\inventory_optimization\io_mvp_1\server\data\Multi_Sku.xlsx"
lead_path = r"C:\Users\UserR93\Desktop\inv\inventory_optimization\io_mvp_1\server\data\Leadtime_MultiSKU.xlsx"
cost_path = r"C:\Users\UserR93\Desktop\inv\inventory_optimization\io_mvp_1\server\data\Node_Costs.xlsx"

base_output_dir = Path(".//output_data")

monthly_demand_path = base_output_dir/"monthly_demand"
calculated_metrics_path = base_output_dir/"calculated_metrics"
distribution_path = base_output_dir/"distribution"
schedule_path = base_output_dir/"schedule_data"
cost_path  = base_output_dir/"cost"

for path in [monthly_demand_path, calculated_metrics_path, distribution_path, schedule_path,cost_path]:
    path.mkdir(parents=True, exist_ok=True)