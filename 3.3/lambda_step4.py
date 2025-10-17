import json
import boto3
import os
import csv
from io import StringIO
from datetime import datetime
import requests

def extract_important_fields(data):
    """
    Extract only important fields from JSON
    """
    d = data.get('data', {})
    
    # Extract parameters
    params = {}
    for group in d.get('parameter_groups', []):
        for param in group.get('parameters', []):
            params[param.get('id')] = param.get('value')
    
    return {
        'ad_id': d.get('ad_id'),
        'subject': d.get('subject'),
        'price': d.get('price', {}).get('value'),
        'list_time': d.get('list_time'),
        'share_url': d.get('share_url'),
        'seller_name': d.get('advertiser', {}).get('name'),
        'seller_type': d.get('advertiser', {}).get('type'),
        'brand': params.get('car_brand') or params.get('cx_make'),
        'model': params.get('level_1') or params.get('cx_model'),
        'year': params.get('regdate'),
        'mileage': params.get('mileage'),
        'fuel': params.get('fuel'),
        'gearbox': params.get('gearbox'),
        'location': d.get('map', {}).get('label'),
        'zipcode': d.get('zipcode')
    }

def download_json_from_link(link):
    """
    Download JSON data from Blocket API
    """
    ad_id = link.split('/')[-1]
    api_url = f"https://api.blocket.se/search_bff/v2/content/{ad_id}?include=store&include=partner_placements&include=breadcrumbs&include=archived&include=car_condition&include=home_delivery&include=realestate&status=active&status=deleted&status=hidden_by_user"
    
    headers = {
        'accept': '*/*',
        'authorization': 'Bearer cddf05ba800457e50f7e1ac74b762738c536cb84',
        'referer': 'https://www.blocket.se/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(api_url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

def save_to_s3(bucket, key, data):
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket, Key=key, Body=data)

def lambda_handler(event, context):
    s3_bucket = os.environ.get('S3_BUCKET_NAME', 'blocked-data-15')
    s3_prefix = os.environ.get('S3_PREFIX', 'flat/')
    
    processed = 0
    failed = 0
    
    for record in event['Records']:
        try:
            message = json.loads(record['body'])
            link = message['link']
            
            print(f"Processing link: {link}")
            
            json_data = download_json_from_link(link)
            row_data = extract_important_fields(json_data)
            
            # Convert to CSV
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=row_data.keys())
            writer.writeheader()
            writer.writerow(row_data)
            csv_data = output.getvalue()
            
            # Save to S3
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ad_id = link.split('/')[-1]
            s3_key = f"{s3_prefix}{ad_id}_{timestamp}.csv"
            
            save_to_s3(s3_bucket, s3_key, csv_data)
            print(f"Saved to s3://{s3_bucket}/{s3_key}")
            processed += 1
                
        except Exception as e:
            print(f"Error processing {link}: {str(e)}")
            failed += 1
    
    return {
        'statusCode': 200,
        'body': json.dumps({'processed': processed, 'failed': failed})
    }
