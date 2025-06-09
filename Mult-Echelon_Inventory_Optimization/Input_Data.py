import pandas as pd
import os

def load_file_as_dataframe(file_path, date_col=None):
    """
    Load a file (CSV, Excel, TSV) into a pandas DataFrame with cleaned column names.
    Optionally parse the date column.
    """
    ext = os.path.splitext(file_path)[-1].lower()

    try:
        if ext == '.csv':
            df = pd.read_csv(file_path, encoding='utf-8', engine='python')
        elif ext == '.tsv':
            df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
        elif ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

        # Clean column names
        df.columns = df.columns.str.strip().str.replace(r'\s+', '_', regex=True).str.replace(r'[\[\]\.]+', '', regex=True)

        if date_col:
            cleaned_date_col = date_col.strip().replace(" ", "_").replace(".", "").replace("[", "").replace("]", "")
            if cleaned_date_col in df.columns:
                df[cleaned_date_col] = pd.to_datetime(df[cleaned_date_col], errors='coerce')
            else:
                print(f"Date column '{cleaned_date_col}' not found. Available columns: {df.columns.tolist()}")

        print(f"File loaded successfully with shape: {df.shape}")
        return df

    except Exception as e:
        print(f"Error loading file: {e}")
        return pd.DataFrame()
