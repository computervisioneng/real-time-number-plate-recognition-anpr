import json
import time
import random
import string

import boto3

import util


def random_string():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))


region_name = 'us-east-1'

# define clients
 
s3_client = boto3.client('s3', region_name=region_name)
dynamodb_client = boto3.client('dynamodb', region_name=region_name)
textract_client = boto3.client('textract', region_name=region_name)
sqs_client = boto3.client('sqs', region_name=region_name)

def lambda_handler(event, context):
    
    tic = time.time()
    
    # get object
    bucket_name = event['Records'][0]['s3']['bucket']['name'] 
    filename = event['Records'][0]['s3']['object']['key'] 
    
    print(filename, bucket_name)
    
    car_id_ = int(filename.split('_')[0])
    
    # text detection (initialize textract job)
    s3_object = {'Bucket': bucket_name, 'Name': filename}
    
    while True:
        try:
            response = textract_client.start_document_text_detection(
                DocumentLocation={'S3Object': s3_object}
                )
            break
        except Exception:
            time.sleep(1)
    
    job_id = response['JobId']
    print(job_id)
    
    while True:
        try:
            # get results from textract job
            response = textract_client.get_document_text_detection(JobId=job_id)
            status = response['JobStatus']
            if status in ['SUCCEEDED', 'FAILED']:
                break
        except Exception:
            time.sleep(1)
    
    print(status)
    
    # verify license number complies format 
    if status == 'SUCCEEDED':
        text = ''
        for item in response['Blocks']:
            if item['BlockType'] == 'LINE':
                text += item['Text']
                
        text = text.upper().replace(' ', '').replace('\n', '')
        print(text)
        if util.license_complies_format(text):
            license_plate_number_ = util.format_license(text)
            
            # write to database
            item = {
                'car_id': {'S': str(car_id_)},
                'license_plate_number': {'S': license_plate_number_},
                'time': {'S': str(time.time() - tic)}
            }
            
            response = dynamodb_client.put_item(TableName='license_plate_numbers', Item=item)
            
            # update the sqs queue
            sqs_client.send_message(
                QueueUrl='https://sqs.us-east-1.amazonaws.com/996209742703/RealTimeANPRTutorialQueue.fifo',
                MessageBody=json.dumps({'license_plate': {'track_id': str(car_id_),
                                                    'text':license_plate_number_}
                    
                }),
                MessageGroupId='lambda',
                MessageDeduplicationId=random_string()
                )
                
        else:
            # TODO: implement ! 
            pass
                
    else:
        # TODO: implement !
        pass
    
            
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
