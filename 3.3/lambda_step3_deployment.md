# AWS Lambda Function - S3 to SQS Car Links Extractor

This Lambda function scans all JSON files in an S3 bucket, extracts car links, and sends them to SQS.

## Features

- **Manual Invocation**: Designed for manual Lambda invocation
- **Full Bucket Scan**: Lists and processes all JSON files in specified S3 prefix
- **Car Link Extraction**: Parses JSON data and extracts individual car links
- **Batch SQS Sending**: Sends links to SQS queue in optimized batches (10 messages)
- **Comprehensive Logging**: Detailed error handling and progress tracking
- **Processing Statistics**: Returns detailed statistics on files processed and links sent

## Architecture

```
Manual Invoke → Lambda Function → List S3 Objects → Process JSON Files → Extract Links → Send to SQS
```

## JSON Data Structure

Expected S3 JSON file structure:
```json
{
  "cars": [
    {
      "dealId": "78449824",
      "link": "https://www.blocket.se/annons/78449824",
      "heading": "Iveco Eurocargo Skåp med lyft",
      "price": {"amount": "0 kr"},
      ...
    }
  ]
}
```

## Setup Instructions

### 1. Create SQS Queue

```bash
# Create SQS queue for car links
aws sqs create-queue --queue-name car-links-queue
```

Note the `QueueUrl` from the response.

### 2. Create IAM Role for Lambda

The Lambda function needs permissions for:
- S3: Get objects from bucket
- SQS: Send messages to queue
- CloudWatch Logs: Write logs

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::blocked-data-15/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "sqs:SendMessage",
                "sqs:SendMessageBatch"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
```

### 3. Create Lambda Function

```bash
# Package the function
zip lambda-step3.zip lambda_step3.py

# Create the Lambda function
aws lambda create-function \
    --function-name s3-car-links-extractor \
    --runtime python3.9 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-s3-sqs-role \
    --handler lambda_step3.lambda_handler \
    --zip-file fileb://lambda-step3.zip \
    --environment Variables={SQS_QUEUE_URL=YOUR_QUEUE_URL} \
    --timeout 300 \
    --memory-size 512
```

### 4. Configure S3 Trigger

Add S3 bucket notification to trigger the Lambda:

```bash
# Add S3 bucket notification
aws s3api put-bucket-notification-configuration \
    --bucket blocked-data-15 \
    --notification-configuration '{
        "LambdaConfigurations": [
            {
                "Id": "car-data-uploaded",
                "LambdaFunctionArn": "arn:aws:lambda:REGION:ACCOUNT_ID:function:s3-car-links-extractor",
                "Events": ["s3:ObjectCreated:*"],
                "Filter": {
                    "Key": {
                        "FilterRules": [
                            {
                                "Name": "prefix",
                                "Value": "car-data/"
                            },
                            {
                                "Name": "suffix",
                                "Value": ".json"
                            }
                        ]
                    }
                }
            }
        ]
    }'
```

## Environment Variables

- `SQS_QUEUE_URL`: URL of the SQS queue to send car links to

## SQS Message Format

Each message sent to SQS contains:

```json
{
    "link": "https://www.blocket.se/annons/78449824",
    "source_page": "s3_extraction",
    "batch_id": "batch_1"
}
```

## Processing Flow

1. **S3 Event Trigger**: Lambda triggered when JSON file uploaded to `car-data/` folder
2. **Read JSON**: Downloads and parses the JSON file from S3
3. **Extract Links**: Parses `cars` array and extracts all `link` fields
4. **Batch Send**: Sends links to SQS in batches of 10 for efficiency
5. **Report Results**: Returns processing statistics

## Response Format

```json
{
    "statusCode": 200,
    "body": {
        "message": "Processed 1 files, extracted 100 links, sent 100 to SQS",
        "files_processed": 1,
        "links_extracted": 100,
        "links_sent": 100,
        "failed_sends": 0,
        "success_rate": "100.0%"
    }
}
```

## Manual Testing

You can also invoke the function manually:

```bash
# Test with specific S3 object
aws lambda invoke \
    --function-name s3-car-links-extractor \
    --payload '{
        "Records": [
            {
                "body": "{\"bucket\":\"blocked-data-15\",\"key\":\"car-data/page_8.json\"}"
            }
        ]
    }' \
    response.json
```

## Monitoring

Monitor through CloudWatch:
- **Lambda Metrics**: Invocations, duration, errors
- **S3 Metrics**: Objects processed
- **SQS Metrics**: Messages sent to queue
- **CloudWatch Logs**: Detailed processing logs

## Error Handling

The function handles various scenarios:
- Invalid JSON files
- Missing S3 objects
- SQS send failures
- Malformed car data
- Network timeouts

All errors are logged with detailed information.

## Cost Estimation

- **Lambda**: ~$0.0003 per execution (512MB RAM)
- **S3 GetObject**: ~$0.0004 per 1,000 requests
- **SQS**: ~$0.40 per million messages
- **Total**: Very low cost for processing car data

## Scaling

- **Automatic**: Scales based on S3 upload rate
- **Concurrent**: Multiple files can be processed simultaneously
- **Batching**: Efficient SQS message batching (10 messages per batch)
- **Limits**: AWS Lambda concurrency limits apply

## Integration

This function fits into the data pipeline:
```
Car Search URLs → Lambda 1 → SQS → Lambda 2 → S3 → Lambda 3 → SQS → Final Processing
```
