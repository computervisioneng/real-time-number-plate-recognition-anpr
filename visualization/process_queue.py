import time
import ast
import os
import json
import shutil

import pandas as pd
import boto3


queue_url = 'queue-url'

table_name = 'table-name'

access_key = "access-key"
secret_key = "secret-key"
region_name = 'region-name'

detections_dir = './amazon-kinesis-video-streams-consumer-library-for-python/detections/'
processed_fragments_dir = './amazon-kinesis-video-streams-consumer-library-for-python/processed_fragments/'
license_plates_dir = './amazon-kinesis-video-streams-consumer-library-for-python/license_plates/'
frames_dir = './amazon-kinesis-video-streams-consumer-library-for-python/frames/'

for dir_ in [detections_dir, processed_fragments_dir, license_plates_dir, frames_dir]:
  if os.path.exists(dir_):
      shutil.rmtree(dir_)
  os.makedirs(dir_)

sqs = boto3.client(
                    'sqs',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region_name
)

dynamodb = boto3.client(
                    'dynamodb',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region_name
)

while True:

    # Receive message from SQS queue
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1
    )

    if 'Messages' not in response.keys():
        print('sleeping...')
        time.sleep(3)

    else:

        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']

        message = ast.literal_eval(message['Body'])

        if 'fragment_number' in message.keys():

            primary_key_value = str(message['fragment_number'])

            # Query the table
            response = dynamodb.query(
                TableName=table_name,
                KeyConditionExpression='fragment_number = :key_value',
                ExpressionAttributeValues={
                    ':key_value': {'S': primary_key_value}
                }
            )

            items = response.get('Items', [])

            data = [{key: value['S'] for key, value in item.items()} for item in items]

            # Convert the extracted data to a Pandas DataFrame
            df = pd.DataFrame(data)

            df.to_csv(os.path.join(detections_dir, '{}.csv'.format(str(primary_key_value))), index=False)

            with open(os.path.join(processed_fragments_dir, str(primary_key_value)), 'w') as f:
                pass

        elif 'license_plate' in message.keys():
            license_track_id = message['license_plate']['track_id']
            text = message['license_plate']['text']

            with open(os.path.join(license_plates_dir, '{}_{}'.format(license_track_id, text)), 'w') as f:
                pass

        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )

