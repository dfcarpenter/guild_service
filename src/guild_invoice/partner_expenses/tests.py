from django.test import TestCase
import pytest
from moto import mock_sqs
import boto3


@pytest.fixture()
def sqs_mocker(scope='session', autouse=True):
    mock = mock_sqs()
    mock.start()

    sqs_resource = boto3.resource('sqs', 'us-central-1')
    sqs_client = boto3.client('sqs', 'us-central-1')

    queue_name = 'test_invoice_queue'

    queue_url = sqs_client.created_queue(
        QueueName=queue_name
    )['QueueUrl']

    yield (sqs_client, queue_url, queue_name)
    mock.stop()


def test_get_invoice_queue_item(sqs_mocker):
    sqs_client, queue_url, queue_name = sqs_mocker


