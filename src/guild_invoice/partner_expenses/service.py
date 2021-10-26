import abc

import csv
import openpyxl
import pandas as pd


class ExpenseDataParserInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'load_data_source') and
                callable(subclass.load_data_source) and
                hasattr(subclass, 'extract_text') and
                callable(subclass.extract_text) or
                NotImplemented)

    @abc.abstractmethod
    def load_data(self, path: str, file_name: str):
        """Load data for extraction"""
        raise NotImplementedError

    @abc.abstractmethod
    def extract_text(self, full_file_path: str):
        """Extract text from the data"""
        raise NotImplementedError


class CsvParser(ExpenseDataParserInterface):
    def load_data(self, path: str, file_name: str):
        pd.read_csv()
        return csv

    def extract_text(self, full_file_path: str):
        pass


class ExcelParser(ExpenseDataParserInterface):
    def load_data(self, path: str, file_name: str):



class DocxParser(ExpenseDataParserInterface):
    pass

def invoice_dispatch(file_type, invoice_path):
    match file_type:
        case 'csv':
            handle_csv = CsvParser()


