# AWS Lambda Function - Car Search URL Sender

This Lambda function sends car search URLs (pages 1-400) to an SQS queue for processing.

## Features

- Sends 400 URLs to SQS queue (one per page)
- Uses batch sending (10 messages at a time) for efficiency
- Includes error handling and progress tracking
- Returns detailed response with success/failure counts

## Setup Instructions

### 1. Create SQS Queue

```bash
# Create a standard SQS queue
aws sqs create-queue --queue-name car-search-queue
```

Note the `QueueUrl` from the response.

### 2. Create IAM Role for Lambda

Create an IAM role with the following policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sqs:SendMessage",
                "sqs:SendMessageBatch",
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
zip lambda-function.zip lambda_step1.py

# Create the Lambda function
aws lambda create-function \
    --function-name car-search-url-sender \
    --runtime python3.9 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-sqs-role \
    --handler lambda_step1.lambda_handler \
    --zip-file fileb://lambda-function.zip \
    --environment Variables={SQS_QUEUE_URL=YOUR_QUEUE_URL} \
    --timeout 300 \
    --memory-size 256
```

### 4. Test the Function

```bash
# Invoke the Lambda function
aws lambda invoke \
    --function-name car-search-url-sender \
    --payload '{}' \
    response.json
```

## Message Format

Each SQS message contains:

```json
{
    "page": 1,
    "url": "https://api.blocket.se/motor-search-service/v4/search/car?sortOrder=H%C3%B6gst+miltal&page=1",
    "timestamp": "request-id"
}
```

## Environment Variables

- `SQS_QUEUE_URL`: The URL of your SQS queue

## Response Format

The function returns:

```json
{
    "statusCode": 200,
    "body": {
        "message": "Successfully sent 400 URLs to SQS queue",
        "total_pages": 400,
        "sent_messages": 400,
        "failed_messages": 0,
        "success_rate": "100.0%"
    }
}
```

## Monitoring

Monitor your Lambda function through CloudWatch Logs and SQS metrics to track:
- Function execution time
- Messages sent to queue
- Any failures or errors

## Cost Considerations

- Lambda: ~$0.0002 per execution
- SQS: ~$0.40 per million messages
- Total estimated cost: <$1 for 400 messages
