# Demo change -
# AWS-S3-Analyzer

Simple script to generate AWS S3 Bucket details using Boto3 and AWS Cost Explorer API.
[Boto3](https://boto3.readthedocs.io/) is an AWS SDK for python to enable low-level access to AWS services

# Setup

1) Install the dependencies:

  $ pip install -r requirements.txt


2) If not already done, set up credentials (in ~/.aws/credentials) by running:

  $ aws configure

See other methods of configuring credentials [here](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html)



# Usage

Run the script as is to get the output for all your S3 buckets associated to that account:

  $ python s3_bucket_analyzer.py > s3_bucket_analysis.csv

You can retrieve details for a specific bucket by specifying the bucket name as an environment variable argurment like so:

  $ python s3_bucket_analyzer.py BUCKET_NAME > s3_bucket_analysis_BUCKET_NAME.csv

You will get a result as long as the bucket exists!
