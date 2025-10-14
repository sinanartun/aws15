import json
import boto3
import requests
import os
from urllib.parse import urlparse
from botocore.exceptions import ClientError

# Initialize AWS clients
s3_client = boto3.client('s3')

# S3 bucket name
S3_BUCKET = 'binance-stockholm'

def lambda_handler(event, context):
    """Lambda function to download files from URLs in SQS messages and save to S3"""
    print(f"Received event: {json.dumps(event, indent=2)}")

    try:
        # Process each record in the SQS event
        processed_files = []
        failed_files = []

        for record in event['Records']:
            try:
                # Extract URLs from message body (it's a JSON string containing an array)
                message_body = record['body']
                urls = json.loads(message_body)

                print(f"Processing {len(urls)} URLs from message: {record['messageId']}")

                # Process each URL in the message
                for url in urls:
                    try:
                        result = download_and_upload_file(url)
                        if result['success']:
                            processed_files.append(result)
                            print(f"Successfully processed: {url}")
                        else:
                            failed_files.append({'url': url, 'error': result['error']})
                            print(f"Failed to process: {url} - {result['error']}")

                    except Exception as e:
                        failed_files.append({'url': url, 'error': str(e)})
                        print(f"Error processing URL {url}: {str(e)}")

            except json.JSONDecodeError as e:
                print(f"Failed to parse message body as JSON: {message_body}")
                failed_files.append({'message_id': record['messageId'], 'error': f"JSON decode error: {str(e)}"})
            except Exception as e:
                print(f"Error processing message {record['messageId']}: {str(e)}")
                failed_files.append({'message_id': record['messageId'], 'error': str(e)})

        # Return summary
        response_body = {
            'processed_files': processed_files,
            'failed_files': failed_files,
            'total_processed': len(processed_files),
            'total_failed': len(failed_files)
        }

        status_code = 200 if len(failed_files) == 0 else 207  # 207 = Multi-Status

        return {
            'statusCode': status_code,
            'body': json.dumps(response_body, indent=2)
        }

    except Exception as e:
        print(f"Critical error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Critical error: {str(e)}',
                'event': event
            })
        }

def download_and_upload_file(url):
    """Download file from URL and upload to S3 bucket"""
    try:
        # Extract filename from URL for S3 key
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)

        # If no filename in URL, create one from the path
        if not filename:
            filename = parsed_url.path.strip('/').replace('/', '-') + '.zip'

        # Ensure we have a .zip extension
        if not filename.endswith('.zip'):
            filename += '.zip'

        s3_key = f"binance-data/{filename}"

        print(f"Downloading {url} and uploading to s3://{S3_BUCKET}/{s3_key}")

        # Download file with streaming to handle large files
        response = requests.get(url, stream=True, timeout=300)  # 5 minute timeout
        response.raise_for_status()

        # Get file size for logging
        file_size = len(response.content) if hasattr(response, 'content') else 'unknown'

        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=response.content,
            ContentType='application/zip',
            Metadata={
                'source_url': url,
                'original_filename': filename
            }
        )

        return {
            'success': True,
            'url': url,
            's3_key': s3_key,
            's3_bucket': S3_BUCKET,
            'file_size': file_size
        }

    except requests.exceptions.RequestException as e:
        error_msg = f"Download failed: {str(e)}"
        print(error_msg)
        return {
            'success': False,
            'url': url,
            'error': error_msg
        }

    except ClientError as e:
        error_msg = f"S3 upload failed: {str(e)}"
        print(error_msg)
        return {
            'success': False,
            'url': url,
            'error': error_msg
        }

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        return {
            'success': False,
            'url': url,
            'error': error_msg
        }
