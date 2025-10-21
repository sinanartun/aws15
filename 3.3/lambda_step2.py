import json
import boto3
import requests
import os
from botocore.exceptions import ClientError
from urllib.parse import urlparse, parse_qs

def download_car_data(url, headers=None):
    """
    Download car data from the given URL
    """
    if headers is None:
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,tr;q=0.8,sv;q=0.7",
            "authorization": "Bearer 68b344934a3e82790b9982eb654790b69a14bde5",
            "cache-control": "max-age=0",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site"
        }

    try:
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to download data from {url}. Status code: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error downloading data from {url}: {str(e)}")
        return None

def save_to_s3(data, bucket_name, key):
    """
    Save JSON data to S3 bucket
    """
    try:
        s3_client = boto3.client('s3')

        # Convert data to JSON string
        json_data = json.dumps(data, ensure_ascii=False, indent=2)

        # Upload to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json_data,
            ContentType='application/json'
        )

        print(f"Successfully saved data to s3://{bucket_name}/{key}")
        return True

    except ClientError as e:
        print(f"Error saving to S3: {str(e)}")
        return False

def extract_page_from_url(url):
    """
    Extract page number from URL
    """
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        page = query_params.get('page', ['unknown'])[0]
        return page
    except Exception as e:
        print(f"Error extracting page from URL {url}: {str(e)}")
        return 'unknown'

def lambda_handler(event, context):
    """
    AWS Lambda function to process SQS messages containing car search URLs,
    download data, and save to S3
    """

    # Get S3 bucket name from environment variable
    s3_bucket = os.environ.get('S3_BUCKET_NAME')

    if not s3_bucket:
        print("Error: S3_BUCKET_NAME environment variable not set")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'S3_BUCKET_NAME environment variable not set'
            })
        }

    processed_messages = 0
    successful_downloads = 0
    failed_downloads = 0

    # Process each SQS record
    for record in event.get('Records', []):
        try:
            # Parse the message body
            message_body = json.loads(record['body'])
            page = message_body.get('page')
            url = message_body.get('url')
            timestamp = message_body.get('timestamp', 'unknown')

            if not url:
                print(f"Warning: No URL found in message {record.get('messageId', 'unknown')}")
                continue

            print(f"Processing message for page {page}: {url}")

            # Download data from the URL
            data = download_car_data(url)

            if data is None:
                failed_downloads += 1
                print(f"Failed to download data for page {page}")
                continue

            # Create S3 key (folder structure: car-data/page_XXX.json)
            if page:
                s3_key = f"car-data/page_{page}.json"
            else:
                # Fallback: extract page from URL
                extracted_page = extract_page_from_url(url)
                s3_key = f"car-data/page_{extracted_page}.json"

            # Save data to S3
            success = save_to_s3(data, s3_bucket, s3_key)

            if success:
                successful_downloads += 1
            else:
                failed_downloads += 1

            processed_messages += 1

        except json.JSONDecodeError as e:
            print(f"Error parsing message body: {str(e)}")
            failed_downloads += 1
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            failed_downloads += 1

    # Return summary
    result = {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Processed {processed_messages} SQS messages',
            'processed_messages': processed_messages,
            'successful_downloads': successful_downloads,
            'failed_downloads': failed_downloads,
            'success_rate': f"{(successful_downloads/processed_messages)*100:.1f}%" if processed_messages > 0 else "0%"
        })
    }

    print(f"Lambda execution completed: {result['body']}")
    return result
