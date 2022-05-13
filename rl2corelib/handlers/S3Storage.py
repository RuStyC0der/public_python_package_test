import boto3
from botocore.exceptions import ClientError


class S3Storage:
    def __init__(self, bucket_name, aws_access_key_id=None, aws_secret_access_key=None, aws_region=None):
        self.bucket_name = bucket_name
        self.client = boto3.client('s3', region_name=aws_region, aws_access_key_id=aws_access_key_id,
                                   aws_secret_access_key=aws_secret_access_key)

    def upload_file(self, filepath_or_obj, key):
        if isinstance(filepath_or_obj, str):
            with open(filepath_or_obj, 'rb') as data:
                self.client.upload_fileobj(data, self.bucket_name, key)
        else:
            self.client.upload_fileobj(filepath_or_obj, self.bucket_name, key)

    def download_file(self, key, file_name, return_body=False):
        obj = self.client.get_object(Bucket=self.bucket_name, Key=key)

        with open(file_name, 'wb') as f:
            body = obj['Body'].read()
            f.write(body)
            if return_body:
                return body
        return file_name

    def get_file(self, key):
        obj = self.client.get_object(Bucket=self.bucket_name, Key=key)
        return obj['Body'].read()

    def is_file_exist(self, key):
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
        except ClientError:
            return False
        return True
