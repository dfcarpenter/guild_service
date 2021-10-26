import os

import boto3

REGION = os.getenv('AWS_REGION', 'us-central-1')

sqs_resource = boto3.resource('sqs', REGION)
sqs_client = boto3.client('sqs', REGION)

def receive_invoice_item(queue_name):
    queue = sqs_resource.get_queue_by_name(QueueName=queue_name)
    queue_url = queue.url

    response = sqs_client.receive_message(
        QueueUrl = queue_url,
        MaxNumberOfMessages=1,
        VisibilityTimeout=10,
        WaitTimeSeconds=3
    )

    try:
        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']
        delete_response = sqs_client.delete_message(QueueUrl=queue_url,
                                               ReceiptHandle=receipt_handle)
        return message['Body']
    except Exception as e:
        print("error in get_queue_item: ")
        print(e)
        return False
