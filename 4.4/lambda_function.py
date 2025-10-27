import json
import boto3
import mysql.connector
import csv
from io import StringIO

def lambda_handler(event, context):
    try:
        print("Lambda function started")
        s3 = boto3.client('s3')
        
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        print(f"Bucket: {bucket}, Key: {key}")
        
        # Get CSV from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        csv_content = response['Body'].read().decode('utf-8')
        print("CSV file downloaded from S3")
        
        # Parse CSV
        csv_reader = csv.DictReader(StringIO(csv_content))
        
        # Connect to RDS
        print("Connecting to RDS...")
        connection = mysql.connector.connect(
            host='database-1.c1ueeskysdez.eu-north-1.rds.amazonaws.com',
            user='admin',
            password='haydegidelum',
            port=63306,
            database='cars'
        )
        print("Connected to RDS")
        
        cursor = connection.cursor()
        
        # Insert data
        insert_query = """
        INSERT INTO cars (ad_id, price, subject, brand, model, model_family, model_year, mileage, 
                          fuel, gearbox, horsepower, color, drive_wheels, body_type, 
                          first_traffic_date, equipment_count, advertiser_type, region, municipality)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        row_count = 0
        for row in csv_reader:
            cursor.execute(insert_query, (
                row['ad_id'], row['price'], row['subject'], row['brand'], row['model'],
                row['model_family'], row['model_year'], row['mileage'], row['fuel'],
                row['gearbox'], row['horsepower'], row['color'], row['drive_wheels'],
                row['body_type'], row['first_traffic_date'], row['equipment_count'],
                row['advertiser_type'], row['region'], row['municipality']
            ))
            row_count += 1
        
        connection.commit()
        print(f"Inserted {row_count} rows")
        
        cursor.close()
        connection.close()
        print("Connection closed")
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Data inserted successfully: {row_count} rows')
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
