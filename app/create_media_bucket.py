from helpers.storage import s3_client 
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv('./app/secrets/.env')

def create_bucket(bucket_name):

    # Check if the bucket exists, if not create it
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError:
        try:
            s3_client.create_bucket(Bucket=bucket_name)            
            
            # Set CORS configuration
            cors_configuration = {
                'CORSRules': [{
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
                    'AllowedOrigins': [os.getenv('FRONTEND_URL', 'http://localhost:3000')],
                    'ExposeHeaders': ['ETag']
                }]
            }
            s3_client.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=cors_configuration)
            
        except ClientError as e:
            print("Failed to create bucket")
            print(str(e))

if __name__ == "__main__":
    bucket_name = os.getenv("B2_BUCKET")
    if bucket_name:
        print("Creating bucket:", bucket_name)
        create_bucket(bucket_name)