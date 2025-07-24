from pathlib import Path

input_path = r"io_mvp_1\server\data\Multi_Sku.xlsx"


base_output_dir = Path("./io_mvp_1/server/output_data")

monthly_demand_path = base_output_dir/"monthly_demand"
calculated_metrics_path = base_output_dir/"calculated_metrics"
distribution_path = base_output_dir/"distribution"
schedule_path = base_output_dir/"schedule_data"
cost_path  = base_output_dir/"cost"

for path in [monthly_demand_path, calculated_metrics_path, distribution_path, schedule_path,cost_path]:
    path.mkdir(parents=True, exist_ok=True)