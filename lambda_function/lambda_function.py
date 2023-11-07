import json
import time
import urllib.parse
import json
import string
import random

import boto3

from util import license_complies_format, format_license


def random_string(N=20):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))


region_name = 'region-name'

s3_client = boto3.client('s3', region_name=region_name)

textract = boto3.client('textract')

dynamodb_client = boto3.client('dynamodb', region_name=region_name)

sqs_client = boto3.client('sqs', region_name=region_name)

queue_url = 'queue-url'

def lambda_handler(event, context):
    
    tic = time.time()
    
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    document_name = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    track_id_ = int(document_name.split('_')[0])
    
    # Define the S3 object containing the image
    s3_object = {'Bucket': bucket_name, 'Name': document_name}
    
    tic = time.time()
    # Start the Textract analysis job
    error = True
    while error:
        try:
            response = textract.start_document_text_detection(
                DocumentLocation={'S3Object': s3_object}
            )
            error = False
        except Exception:
            time.sleep(1)
    
    # Get the JobId from the response
    job_id = response['JobId']
    
    # Poll the job status until it's complete
    while True:
        try:
            response = textract.get_document_text_detection(JobId=job_id)
            status = response['JobStatus']
            if status in ['SUCCEEDED', 'FAILED']:
                break
        except Exception:
            time.sleep(1)
    
    # If the job is successful, retrieve the results
    if status == 'SUCCEEDED':
        # Extract and print the detected text
        text = ""
        for item in response['Blocks']:
            if item['BlockType'] == 'LINE':
                text += item['Text']
                
        text = text.upper().replace(' ', '').replace('\n', '')

        if license_complies_format(text):
            license_plate_number_ = format_license(text)
            
            tac = time.time()
            
            item = {
                'car_id': {'S': str(track_id_)},
                'license_plate_number': {'S': license_plate_number_},
                'time': {'S': str(tac - tic)}
            }
            
            response = dynamodb_client.put_item(TableName='table-name', Item=item)
            
            response = sqs_client.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps({'license_plate': {'track_id': str(track_id_), 'text': license_plate_number_}}),
                    MessageGroupId='{}_{}'.format(str(track_id_), license_plate_number_),
                    MessageDeduplicationId=random_string()
                )

            
        else:
            # TODO: HANDLE READING ERROR !
            pass

    else:
        print('Textract job failed.')
        
    print(time.time() - tic)
    
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
