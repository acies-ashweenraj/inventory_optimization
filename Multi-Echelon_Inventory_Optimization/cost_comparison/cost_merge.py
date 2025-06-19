import pandas as pd


def cost_merge_function(eoq_df,non_eoq_df):
        merged_df = pd.merge(
        eoq_df,
        non_eoq_df[["Echelon", "Year", "Month", "total_cost_non_eoq"]],
        on=["Echelon", "Year", "Month"],
        how="left"
    )
        print(merged_df.head())
        return merged_df