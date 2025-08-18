import pandas as pd
import numpy as np

def get_meio_cost():
    """Simulate MEIO output (replace with your MEIO pipeline output)."""
    data = {
        "SKU_ID": [f"SKU_{i}" for i in range(1, 11)],
        "Location_ID": [f"LOC_{(i%3)+1}" for i in range(1, 11)],
        "Total_Cost_meio": np.random.randint(800, 1500, 10)
    }
    return pd.DataFrame(data)

def get_non_meio_cost(meio_df: pd.DataFrame):
    """Generate Non-MEIO baseline cost (naïve, higher than MEIO)."""
    non_meio = meio_df.copy()
    non_meio = non_meio.drop(columns=["Total_Cost_meio"])
    # Assume non-MEIO costs are higher by 10–30%
    non_meio["Total_Cost_non_meio"] = meio_df["Total_Cost_meio"] * np.random.uniform(1.1, 1.3, len(meio_df))
    return non_meio

def compare_meio_vs_non_meio(meio_cost_df: pd.DataFrame, non_meio_cost_df: pd.DataFrame):
    """Compare MEIO vs Non-MEIO costs."""

    merged = pd.merge(
        non_meio_cost_df,
        meio_cost_df,
        on=["SKU_ID", "Location_ID"],
        how="inner"
    )

    merged["Cost_Saving"] = merged["Total_Cost_non_meio"] - merged["Total_Cost_meio"]
    merged["Saving_%"] = (merged["Cost_Saving"] / merged["Total_Cost_non_meio"]) * 100

    summary = {
        "total_cost_non_meio": merged["Total_Cost_non_meio"].sum(),
        "total_cost_meio": merged["Total_Cost_meio"].sum(),
        "total_saving": merged["Cost_Saving"].sum(),
        "saving_percent": (merged["Cost_Saving"].sum() / merged["Total_Cost_non_meio"].sum()) * 100,
        "comparison_df": merged
    }

    return summary
