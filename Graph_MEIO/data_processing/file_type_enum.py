from enum import Enum
import pandas as pd

class FileType(Enum):
    CSV = ('.csv', lambda path: pd.read_csv(path, encoding='utf-8', engine='python'))
    TSV = ('.tsv', lambda path: pd.read_csv(path, sep='\t', encoding='utf-8'))
    XLS = ('.xls', lambda path: pd.read_excel(path, engine='openpyxl'))
    XLSX = ('.xlsx', lambda path: pd.read_excel(path, engine='openpyxl'))

    def __init__(self, extension, reader_function):
        self.extension = extension
        self.reader_function = reader_function

    @staticmethod
    def get_reader(ext):
        for filetype in FileType:
            if ext == filetype.extension:
                return filetype.reader_function
        raise ValueError(f"Unsupported file extension: {ext}")
