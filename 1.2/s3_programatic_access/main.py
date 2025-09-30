import boto3

client = boto3.client('s3')


# for i in range(10):

#     response = client.create_bucket(
#         Bucket='bubenimyenibucket' + str(i),
#         CreateBucketConfiguration={
#             'LocationConstraint': 'eu-north-1',
#         },
#     )

#     print(response)


response = client.put_object(
    Body='1.png',
    Bucket='bubenimyenibucket',
    Key='1.png',
    ServerSideEncryption='AES256',
    StorageClass='STANDARD_IA',
)
