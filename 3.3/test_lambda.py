import json
import os
import sys
from unittest.mock import Mock, MagicMock

# Mock the Lambda environment
class MockContext:
    def __init__(self):
        self.aws_request_id = "test-request-12345"

# Mock SQS client for testing
def mock_sqs_client():
    mock_client = MagicMock()
    mock_client.send_message_batch.return_value = {
        'Successful': [{'Id': '1'}, {'Id': '2'}],
        'Failed': []
    }
    return mock_client

def test_lambda_function():
    """Test the Lambda function locally"""

    # Add current directory to path to import lambda function
    sys.path.insert(0, '.')

    # Mock environment variable
    os.environ['SQS_QUEUE_URL'] = 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'

    # Import the lambda function
    import lambda_step1

    # Mock boto3
    import boto3
    original_client = boto3.client
    boto3.client = mock_sqs_client

    try:
        # Create mock context
        context = MockContext()

        # Test the lambda function with a mock event
        event = {}

        result = lambda_step1.lambda_handler(event, context)

        # Parse the response
        response_body = json.loads(result['body'])

        print("✅ Lambda function test completed successfully!")
        print(f"Status Code: {result['statusCode']}")
        print(f"Message: {response_body['message']}")
        print(f"Sent Messages: {response_body['sent_messages']}")
        print(f"Failed Messages: {response_body['failed_messages']}")
        print(f"Success Rate: {response_body['success_rate']}")

        # Verify results
        assert result['statusCode'] == 200
        assert response_body['sent_messages'] == 400
        assert response_body['failed_messages'] == 0
        assert response_body['total_pages'] == 400

        print("✅ All assertions passed!")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

    finally:
        # Restore original boto3 client
        boto3.client = original_client

    return True

if __name__ == "__main__":
    success = test_lambda_function()
    if success:
        print("\n🎉 Local test passed! Ready to deploy to AWS.")
    else:
        print("\n💥 Local test failed. Please check the code.")
        sys.exit(1)
