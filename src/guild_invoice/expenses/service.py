import os
import abc

import posixpath

import boto3
from botocore.exceptions import ClientError

import csv
import openpyxl
import pandas as pd

from django.core.exceptions import (
    ImproperlyConfigured, SuspiciousFileOperation,
)

from .models import PartnerExpenses

s3_client = boto3.client('s3')
BUCKET = os.getenv('AWS_INVOICE_BUCKET', 'guild-expense-bucket')




class ExpenseDataParserInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'load_data_source') and
                callable(subclass.load_data_source) and
                hasattr(subclass, 'extract_expense') and
                callable(subclass.extract_text) or
                NotImplemented)

    @abc.abstractmethod
    def load_data(self, path: str, file_name: str):
        """Load data for extraction"""
        raise NotImplementedError

    @abc.abstractmethod
    def extract_expense(self, full_file_path: str):
        """Extract expense from the data"""
        raise NotImplementedError


class CsvParser(ExpenseDataParserInterface):
    def load_data(self, path: str, file_name: str):
        pd.read_csv()
        return csv

    def extract_expense(self, full_file_path: str):
        self.load_data()


class ExcelParser(ExpenseDataParserInterface):
    """
    If we use pandas ( which is great ) we will need to convert from a dataframe to a dict in order to properly save

    df_expenses = df.to_dict('expenses')

    model_instances = [PartnerExpenses(
        expense_amount=record['field_1'],
        customer_user_id=record['field_2'],
    ) for record in df_records]

    PartnerExpenses.objects.bulk_create(model_instances)

    """
    def load_data(self, path: str, file_name: str): pass

    def extract_expense(self, full_file_path: str): pass


class DocxParser(ExpenseDataParserInterface): pass


def get_expense(expense_path: str) -> str:
    try:
        obj = s3_client.get_object(BUCKET, expense_path)
        return obj
    except ClientError as e:
        error_code = e.response["Error"]["Code"]


def expense_process_dispatch(file_type, invoice_data):
    match file_type:
        case 'csv':
            csv = CsvParser()
            csv.extract_expense(invoice_data)
        case 'xlsx':
            xlsx = ExcelParser()
            xlsx.extract_expense(invoice_data)
        case 'docx':
            pass
        case _:
            csv = CsvParser()
            csv.extract_expense(invoice_data)


def save_expense(payload: dict):

    pluck = lambda dict, *args: (dict[arg] for arg in args)

    try:
        name, path = pluck(payload, 'name', 'path')
        expense = get_expense()
        expense_process_dispatch()
    except IndexError:
        pass

    else:
        PartnerExpenses.save()



def clean_name(name):
    """
    Cleans the name so that Windows style paths work
    """
    # Normalize Windows style paths
    clean_name = posixpath.normpath(name).replace('\\', '/')

    # os.path.normpath() can strip trailing slashes so we implement
    # a workaround here.
    if name.endswith('/') and not clean_name.endswith('/'):
        # Add a trailing slash as it was stripped.
        clean_name = clean_name + '/'

    # Given an empty string, os.path.normpath() will return ., which we don't want
    if clean_name == '.':
        clean_name = ''

    return clean_name







