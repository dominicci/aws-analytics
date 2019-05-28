# aws-s3-analyzer
Simple script to generate AWS S3 Bucket details using Boto3 and AWS Cost Explorer API.

# Usage:
First, install the dependencies:

$ pip install boto3

$ pip install hurry.filesize

Next, if not already done, set up credentials (in e.g. ~/.aws/credentials) by running:

$ aws configure

Finally, run the script to get the output for all your buckets:

$ python s3_bucket_analyzer.py
