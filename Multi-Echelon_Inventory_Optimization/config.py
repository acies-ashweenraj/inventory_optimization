from pathlib import Path

input_path = r"C:\Users\DELL\Desktop\project-1 R&S\inventory_optimization\Multi-Echelon_Inventory_Optimization\data\Sample_2.csv"


# Output base directory
base_output_dir = Path("./Multi-Echelon_Inventory_Optimization/output_data")

# Define subfolders
monthly_demand_path = base_output_dir / "monthly_demand"
calculated_metrics_path = base_output_dir / "calculated_metrics"
distribution_path = base_output_dir / "distribution"
schedule_path = base_output_dir / "schedule_data"

# Ensure all folders exist
for path in [monthly_demand_path, calculated_metrics_path, distribution_path, schedule_path]:
    path.mkdir(parents=True, exist_ok=True)