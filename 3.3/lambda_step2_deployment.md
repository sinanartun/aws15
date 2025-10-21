# AWS Lambda Function - Car Data Downloader

This Lambda function processes SQS messages containing car search URLs, downloads the data, and saves it to S3.

## Features

- Processes SQS messages from the car search URL queue
- Downloads car data from blocket.se API
- Saves JSON data to S3 bucket with organized folder structure
- Includes error handling and detailed logging
- Returns processing statistics

## Architecture

```
SQS Queue → Lambda Function → Download Data → Save to S3
```

## Message Format

Expected SQS message body:
```json
{
    "page": 5,
    "url": "https://api.blocket.se/motor-search-service/v4/search/car?sortOrder=H%C3%B6gst+miltal&page=5",
    "timestamp": "470a4a17-da36-4cad-aef8-9315bdefc7ec"
}
```

## Setup Instructions

### 1. Create S3 Bucket

```bash
# Create S3 bucket for storing car data
aws s3 mb s3://your-car-data-bucket-name
```

### 2. Create IAM Role for Lambda

The Lambda function needs permissions for:
- SQS: Receive messages and delete processed messages
- S3: Put objects
- CloudWatch Logs: Write logs

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

### 3. Create Lambda Function

```bash
# Package the function
zip lambda-step2.zip lambda_step2.py

# Create the Lambda function
aws lambda create-function \
    --function-name car-data-downloader \
    --runtime python3.9 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-sqs-s3-role \
    --handler lambda_step2.lambda_handler \
    --zip-file fileb://lambda-step2.zip \
    --environment Variables={S3_BUCKET_NAME=your-bucket-name} \
    --timeout 300 \
    --memory-size 512
```

### 4. Configure SQS Trigger

Add SQS as a trigger for the Lambda function:

```bash
aws lambda create-event-source-mapping \
    --function-name car-data-downloader \
    --event-source-arn arn:aws:sqs:REGION:ACCOUNT_ID:car-search-queue \
    --batch-size 10 \
    --maximum-batching-window-in-seconds 60
```

## Environment Variables

- `S3_BUCKET_NAME`: Name of the S3 bucket to store car data

## S3 Storage Structure

Data is stored in S3 with the following structure:
```
s3://your-bucket-name/
└── car-data/
    ├── page_1.json
    ├── page_2.json
    ├── page_3.json
    └── ...
```

## Response Format

The function returns processing statistics:

```json
{
    "statusCode": 200,
    "body": {
        "message": "Processed 10 SQS messages",
        "processed_messages": 10,
        "successful_downloads": 9,
        "failed_downloads": 1,
        "success_rate": "90.0%"
    }
}
```

## Monitoring

Monitor through CloudWatch:
- Lambda metrics: invocations, duration, errors
- SQS metrics: messages processed, dead letter queue
- S3 metrics: objects created

## Error Handling

The function handles various error scenarios:
- Invalid SQS message format
- Network errors when downloading data
- S3 upload failures
- Missing environment variables

All errors are logged to CloudWatch Logs.

## Cost Estimation

- Lambda: ~$0.0003 per execution (with 512MB RAM)
- SQS: ~$0.40 per million messages
- S3: ~$0.023 per GB stored
- Total: Very low cost for processing car data

## Scaling

The function automatically scales based on SQS queue depth:
- More messages = more concurrent Lambda executions
- Batch size of 10 messages for efficiency
- 60-second batching window for optimal throughput
