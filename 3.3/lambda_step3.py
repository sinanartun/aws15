import json
import boto3
import os
from botocore.exceptions import ClientError

def extract_car_links(data):
    """
    Extract car links from JSON data
    """
    links = []
    if 'cars' in data:
        for car in data['cars']:
            if 'link' in car:
                links.append(car['link'])
    return links

def send_links_to_sqs(links, queue_url):
    """
    Send car links to SQS queue in batches
    """
    if not links:
        return 0, 0

    sqs = boto3.client('sqs')
    sent = 0
    failed = 0

    for i in range(0, len(links), 10):
        batch = links[i:i + 10]
        entries = [{'Id': str(j), 'MessageBody': json.dumps({'link': link})} 
                   for j, link in enumerate(batch)]

        try:
            response = sqs.send_message_batch(QueueUrl=queue_url, Entries=entries)
            sent += len(response.get('Successful', []))
            failed += len(response.get('Failed', []))
        except ClientError as e:
            print(f"Error sending batch: {str(e)}")
            failed += len(batch)

    return sent, failed

def read_json_from_s3(bucket, key):
    """
    Read JSON file from S3 bucket
    """
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(response['Body'].read().decode('utf-8'))

def list_s3_json_files(bucket, prefix=''):
    """
    List all JSON files in S3 bucket
    """
    s3 = boto3.client('s3')
    json_files = []
    paginator = s3.get_paginator('list_objects_v2')
    
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
    
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                if obj['Key'].endswith('.json'):
                    json_files.append(obj['Key'])
    
    print(f"Found {len(json_files)} JSON files in s3://{bucket}/{prefix}")
    return json_files

def lambda_handler(event, context):
    """
    AWS Lambda function to scan all JSON files in S3 bucket, extract car links, and send to SQS
    """

    # Get environment variables
    sqs_queue_url = os.environ.get('SQS_QUEUE_URL')
    s3_bucket = os.environ.get('S3_BUCKET_NAME', 'blocked-data-15')
    s3_prefix = os.environ.get('S3_PREFIX', '')

    if not sqs_queue_url:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'SQS_QUEUE_URL environment variable not set'
            })
        }

    print(f"Starting scan of s3://{s3_bucket}/{s3_prefix}")

    # List all JSON files in S3
    json_files = list_s3_json_files(s3_bucket, s3_prefix)

    if not json_files:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'No JSON files found in s3://{s3_bucket}/{s3_prefix}',
                'files_processed': 0,
                'links_extracted': 0,
                'links_sent': 0,
                'failed_sends': 0,
                'success_rate': '0%'
            })
        }

    total_links_extracted = 0
    total_links_sent = 0
    total_failed_sends = 0
    files_processed = 0
    files_failed = 0

    # Process each JSON file
    for key in json_files:
        try:
            data = read_json_from_s3(s3_bucket, key)
            links = extract_car_links(data)
            total_links_extracted += len(links)

            sent, failed = send_links_to_sqs(links, sqs_queue_url)
            total_links_sent += sent
            total_failed_sends += failed
            files_processed += 1

            print(f"Processed {key}: {len(links)} links, {sent} sent")
        except Exception as e:
            print(f"Error processing {key}: {str(e)}")
            files_failed += 1

    # Return summary
    result = {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Processed {files_processed} files ({files_failed} failed), extracted {total_links_extracted} links, sent {total_links_sent} to SQS',
            'files_found': len(json_files),
            'files_processed': files_processed,
            'files_failed': files_failed,
            'links_extracted': total_links_extracted,
            'links_sent': total_links_sent,
            'failed_sends': total_failed_sends,
            'success_rate': f"{(total_links_sent/(total_links_sent + total_failed_sends))*100:.1f}%" if (total_links_sent + total_failed_sends) > 0 else "0%"
        })
    }

    print(f"Lambda execution completed: {result['body']}")
    return result
