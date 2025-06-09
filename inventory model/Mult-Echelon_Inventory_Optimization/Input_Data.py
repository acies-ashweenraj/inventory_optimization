import pandas as pd
import os

def load_file_as_dataframe(file_path, date_col=None):
    """
    Load a file (CSV, Excel, TSV) into a pandas DataFrame with cleaned column names.
    
    Parameters:
        file_path (str): Path to the input file
        
    Returns:
        pd.DataFrame: Loaded and cleaned DataFrame
    """
    # Get the file extension
    ext = os.path.splitext(file_path)[-1].lower()
    
    try:
        if ext in ['.csv']:
            df = pd.read_csv(file_path, encoding='utf-8')
        elif ext in ['.tsv']:
            df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, engine='openpyxl')  # or engine='xlrd' for older .xls
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
        
        # Clean column names
        df.columns = df.columns.str.strip()  # remove extra spaces
        df.columns = df.columns.str.replace(r'\s+', '_', regex=True)  # replace spaces with _
        
        print(f"File loaded successfully with shape: {df.shape}")
        return df

    except Exception as e:
        print(f"Error loading file: {e}")
        return pd.DataFrame()  # return empty df on failure
