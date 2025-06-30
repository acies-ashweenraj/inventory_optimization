import pandas as pd
from config import input_path
from data_processing.input import extract_load


def data_processing_func():
    extract_load(input_path)