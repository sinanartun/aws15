import json
import boto3
import csv
import io
import os

# Initialize AWS clients
s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')

# Get SQS queue URL from environment variable
SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL')

def lambda_handler(event, context):
    print(event)
    try:
        # Process each record in the S3 event
        for record in event['Records']:
            # Get bucket and key from S3 event
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']

            print(f"Processing file: s3://{bucket}/{key}")

            # Read CSV file from S3
            csv_content = read_csv_from_s3(bucket, key)

            # Process each line and send to SQS
            process_csv_lines(csv_content, bucket, key)

        return {
            'statusCode': 200,
            'body': json.dumps('Successfully processed CSV and sent to SQS')
        }

    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

def read_csv_from_s3(bucket, key):
    """Read CSV file from S3 bucket"""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        return content
    except Exception as e:
        raise Exception(f"Failed to read CSV from S3: {str(e)}")

def process_csv_lines(csv_content, bucket, key):
    """Process each line of CSV and send to SQS"""
    try:
        # Parse CSV content
        csv_reader = csv.reader(io.StringIO(csv_content))

        # Process each row
        for row_num, row in enumerate(csv_reader, start=1):
            # Skip empty rows
            if not row or not any(field.strip() for field in row):
                continue

            # Convert row to string (you can customize this format)
            row_data = ','.join(row)



            # Send to SQS
            send_to_sqs(row)

            print(f"Processed row {row_num}: {row_data}")

    except Exception as e:
        raise Exception(f"Failed to process CSV lines: {str(e)}")

def send_to_sqs(message_body):
    """Send message to SQS queue"""
    try:
        if not SQS_QUEUE_URL:
            raise Exception("SQS_QUEUE_URL environment variable not set")

        response = sqs_client.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )

        print(f"Message sent to SQS: {response['MessageId']}")

    except Exception as e:
        raise Exception(f"Failed to send message to SQS: {str(e)}")
