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

# New function to load a pickle file as a dataframe
def load_pickle_as_dataframe(pickle_path):
    try:
        if not os.path.exists(pickle_path):
            raise FileNotFoundError(f"❌ File not found: {pickle_path}")

        with open(pickle_path, "rb") as f:
            df = pickle.load(f)

        print("Original columns:", df.columns.tolist())

        if "Time.[Week]" in df.columns:
            df["Time.[Week]"] = pd.to_datetime(df["Time.[Week]"], errors="coerce")

        df.columns = (
            df.columns.str.strip()
                      .str.replace(r'\s+', '_', regex=True)
                      .str.replace(r'[\[\]\.]+', '', regex=True)
        )

        print("Renamed columns:", df.columns.tolist())
        return df

    except Exception as e:
        print(f"❌ Error loading pickle file '{pickle_path}': {e}")
        return pd.DataFrame()