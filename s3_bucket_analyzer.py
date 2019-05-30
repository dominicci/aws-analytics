import boto3
from datetime import datetime, timedelta
from hurry.filesize import size
from tabulate import tabulate

now = datetime.now().replace(tzinfo=None)

# Using AWS' boto3 SDK for python for access to AWS services - https://boto3.readthedocs.io/
# The S3 Client provides low-level access to S3 resources.
# The S3 Resource provides high-level abstraction.
# The Cost Client - Cost Explorer - is part of AWS' Cost Management APIs for billed usage.
s3client = boto3.client('s3')
s3resource = boto3.resource('s3')
cost_client = boto3.client('ce')

# Get a list of all buckets
allbuckets = s3resource.buckets.all()
bucket_size = 0
obj_dict = {}

# Loop through each bucket
for bucket in allbuckets:
    # Retrieve bucket location
    location = s3client.get_bucket_location(Bucket=bucket.name)['LocationConstraint']

    # Retrieve each object in the bucket
    for obj in bucket.objects.all():

        obj_name = obj.key
        obj_age = now - obj.last_modified.replace(tzinfo=None)
        obj_mod = obj.last_modified.replace(tzinfo=None)
        obj_class = obj.storage_class
        more = obj.Object()
        obj_size = more.content_length

        bucket_size += obj_size

        if obj_name.endswith('/'):
            pass

        else:
            obj_dict[obj_name] = {'Name': obj_name, 'Last Modified': obj_mod, \
                'Size': size(obj_size), 'Age in Days': obj_age.days, 'Class': obj_class}

    # List Bucket details
    print(tabulate([['Bucket name','Creation Date','Location','Size','Number of objects'], \
		[bucket.name,bucket.creation_date,location,size(bucket_size),len(obj_dict)]],headers='firstrow'))

    # List objects within the bucket and their details
    print('\nObjects:')
    print(tabulate(obj_dict.values(),headers='keys'))

# Get cost of service using cost explorer
start = (now - timedelta(days=30)).strftime('%Y-%m-%d')
end = now.strftime('%Y-%m-%d')

results = []

token = None

while True:
    if token:
        kwargs = {'NextPageToken': token}
    else:
        kwargs = {}
    data = cost_client.get_cost_and_usage( \
        Filter={'Dimensions': {'Key':'SERVICE', 'Values': ['Amazon Simple Storage Service']}}, \
        TimePeriod={'Start': start, 'End':  end}, \
        Granularity='MONTHLY', Metrics=['UnblendedCost'], \
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'LINKED_ACCOUNT'}, \
                {'Type': 'DIMENSION', 'Key': 'SERVICE'}], **kwargs)

    results += data['ResultsByTime']
    token = data.get('NextPageToken')

    if not token:
        break

# List S3 Cost details
print('\nCost Details')
for result_by_time in results:

    for group in result_by_time['Groups']:
        amount = group['Metrics']['UnblendedCost']['Amount']
        unit = group['Metrics']['UnblendedCost']['Unit']
	print(tabulate([['Service','Amount','Unit'],[group['Keys'].pop(),amount,unit]],headers='firstrow'))
