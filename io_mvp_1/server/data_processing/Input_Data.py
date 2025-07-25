import pandas as pd
import os
from .file_type_enum import FileType
import pickle

def load_file_as_dataframe(file_path, date_col=None):
    ext = os.path.splitext(file_path)[-1].lower()

    try:
    
        reader = FileType.get_reader(ext)
        df = reader(file_path)

        df.columns = (
            df.columns.str.strip()
                      .str.replace(r'\s+', '_', regex=True)
                      .str.replace(r'[\[\]\.]+', '', regex=True)
        )

        if date_col:
            cleaned_date_col = date_col.strip().replace(" ", "_").replace(".", "").replace("[", "").replace("]", "")
            if cleaned_date_col in df.columns:
                df[cleaned_date_col] = pd.to_datetime(df[cleaned_date_col], errors='coerce')
            else:
                print(f"Date column '{cleaned_date_col}' not found. Available columns: {df.columns.tolist()}")

        print(f"File loaded successfully with shape: {df.shape}")
        df["DC"] = "DC_" + df["DC"].astype(str)
        df["Warehouse"] = "Warehouse_" + df["Warehouse"].astype(str)
        df["Store"] = "Store_" + df["Store"].astype(str)
        return df

    except Exception as e:
        print(f"Error loading file: {e}")
        return pd.DataFrame()

# def load_pickle_as_dataframe(pickle_path):
#     try:
#         if not os.path.exists(pickle_path):
#             raise FileNotFoundError(f"❌ File not found: {pickle_path}")

#         with open(pickle_path, "rb") as f:
#             df = pickle.load(f)

#         return df

#     except Exception as e:
#         print(f"❌ Error loading pickle file '{pickle_path}': {e}")
#         return pd.DataFrame()
    


# def load_and_clean_pickle_df(file_path: str, date_col: str = None) -> pd.DataFrame:
#     ext = os.path.splitext(file_path)[-1].lower()

#     try:
#         # Step 1: Load the DataFrame based on file extension
#         if ext in ['.csv']:
#             df = pd.read_csv(file_path)
#         elif ext in ['.xls', '.xlsx']:
#             df = pd.read_excel(file_path)
#         elif ext in ['.pkl', '.pickle']:
#             df = pd.read_pickle(file_path)
#         else:
#             print(f"❌ Unsupported file type: {ext}")
#             return pd.DataFrame()

#         # Step 2: Clean column names
#         df.columns = (
#             df.columns.str.strip()
#                       .str.replace(r'\s+', '_', regex=True)
#                       .str.replace(r'[\[\]\.]+', '', regex=True)
#         )

#         # Step 3: Optional - Convert date column
#         if date_col:
#             cleaned_date_col = (
#                 date_col.strip()
#                         .replace(" ", "_")
#                         .replace(".", "")
#                         .replace("[", "")
#                         .replace("]", "")
#             )
#             if cleaned_date_col in df.columns:
#                 df[cleaned_date_col] = pd.to_datetime(df[cleaned_date_col], errors='coerce')
#             else:
#                 print(f"⚠️ Date column '{cleaned_date_col}' not found. Available: {df.columns.tolist()}")

#         # Step 4: Add DC, Warehouse, Store prefixes if those columns exist
#         for col, prefix in [('DC', 'DC_'), ('Warehouse', 'Warehouse_'), ('Store', 'Store_')]:
#             if col in df.columns:
#                 df[col] = prefix + df[col].astype(str)

#         print(f"✅ File loaded successfully: {file_path} | Shape: {df.shape}")
#         return df

#     except Exception as e:
#         print(f"❌ Error loading file '{file_path}': {e}")
#         return pd.DataFrame()