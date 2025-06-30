import pandas as pd
import os
from .file_type_enum import FileType
from config import extracted_data_path
# from preprocessing import data_processing
from .preprocessing import data_processing

def load_file_as_dataframe(file_path):
    ext = os.path.splitext(file_path)[-1].lower()

    try:
        # Excel file case (multi-sheet support)
        if ext in ['.xls', '.xlsx']:
            df_dict = pd.read_excel(
                file_path,
                sheet_name=None,  # loads all sheets
                engine='openpyxl'
            )
            return df_dict  # Dict of sheet_name -> DataFrame

        # Other file types (CSV, TSV, etc.)
        reader = FileType.get_reader(ext)
        if reader is None:
            raise ValueError(f"No reader defined for extension: {ext}")

        df = reader(file_path)
        return df

    except Exception as e:
        print(f"Error loading file: {e}")
        return {} if ext in ['.xls', '.xlsx'] else pd.DataFrame()
    

def flatten_df(df_dict, scope='global'):
    if scope == 'global':
        target_scope = globals()
    else:
        import inspect
        target_scope = inspect.currentframe().f_back.f_locals

    for sheet_name, df in df_dict.items():
        # Sanitize the sheet name to be a valid variable
        var_name = sheet_name.strip().replace(' ', '_').replace('-', '_')
        target_scope[var_name] = data_processing(df)
        target_scope[var_name].to_excel(f"{extracted_data_path}/{var_name}.xlsx", index=False, engine='openpyxl')
        # print(f"Created variable: {var_name}")


def extract_load(file_path):
    df_dict = load_file_as_dataframe(file_path)
    flatten_df(df_dict)
