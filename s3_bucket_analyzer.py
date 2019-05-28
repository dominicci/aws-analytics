import boto3
from datetime import datetime, timedelta
from hurry.filesize import size

now = datetime.now().replace(tzinfo=None)

s3client = boto3.client('s3')
s3resource = boto3.resource('s3')
cost = boto3.client('ce')


# Get a list of all buckets
allbuckets = s3resource.buckets.all()
bucket_size = 0
obj_dict = {}
obj_count = 0

print('Bucket name'.ljust(25) + 'Created on'.ljust(25) + 'Size'.center(25) + 'Number of objects'.ljust(25))

# Loop through each bucket
for bucket in allbuckets:

    # For each object get details
    for obj in bucket.objects.all():

        more = obj.Object()
        obj_age = now - obj.last_modified.replace(tzinfo=None)
        obj_name = obj.key
        obj_size = more.content_length
        obj_mod = obj.last_modified.replace(tzinfo=None)
        obj_class = obj.storage_class

        bucket_size += obj_size

	if obj_name.endswith('/'):
	    pass

	else:
	    obj_dict[obj_name] = {'name': obj_name, 'modified': obj_mod, \
                'size': size(obj_size), 'age': obj_age.total_seconds(), 'class': obj_class}

	    obj_count += 1

    # List Bucket details
    print('{0:<25}{1}{2:^25}{3:^25}'.format(bucket.name,bucket.creation_date,size(bucket_size),obj_count))

    # List Object details within bucket
    print('Files:')
    for item in obj_dict.values():
	print('Name: {0} \nClass: {1} \nModified: {2} \nAge: {3:0.2f}s \nSize: {4}'.format(item['name'], \
		item['class'], item['modified'], int(item['age']), item['size']))

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
    data = cost.get_cost_and_usage( \
	Filter={'Dimensions': {'Key':'SERVICE', 'Values': ['Amazon Simple Storage Service']}}, \
	TimePeriod={'Start': start, 'End':  end}, \
	Granularity='MONTHLY', Metrics=['UnblendedCost','BlendedCost','UsageQuantity'], \
	GroupBy=[{'Type': 'DIMENSION', 'Key': 'LINKED_ACCOUNT'}, \
		{'Type': 'DIMENSION', 'Key': 'SERVICE'}], **kwargs)

    results += data['ResultsByTime']
    token = data.get('NextPageToken')

    if not token:
        break

# List Cost details
print('Service'.ljust(25) + 'Amount'.center(25) + 'Unit'.center(25))

for result_by_time in results:

    for group in result_by_time['Groups']:
        amount = group['Metrics']['UnblendedCost']['Amount']
        unit = group['Metrics']['UnblendedCost']['Unit']
        print('{0}{1:^25}{2:^25}'.format(group['Keys'].pop(), amount, unit))
