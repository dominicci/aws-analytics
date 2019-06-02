import sys
import boto3
import operator
from datetime import datetime, timedelta
from hurry.filesize import size
from tabulate import tabulate

now = datetime.now().replace(tzinfo=None)

s3client = boto3.client('s3')
s3resource = boto3.resource('s3')
cost_client = boto3.client('ce')

#allbuckets = s3resource.buckets.all()

def retrieve_objects(bucket):
# Loop through each bucket

   #bucket = s3resource.Bucket(bucket_name)
    # print('--->',bucket)
    bucket_size = 0
    obj_dict = {}

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

    return obj_dict, bucket_size

def estimate_s3_costs():

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
    for result in results:
        if len(result['Groups'])!=0:
            amount = result['Groups'][0]['Metrics']['UnblendedCost']['Amount']
	    unit = result['Groups'][0]['Metrics']['UnblendedCost']['Unit']
    return amount, unit

def list_all_buckets(bucket):

    obj_dict, bucket_size = retrieve_objects(bucket)
    amount, unit = estimate_s3_costs()
    location = s3client.get_bucket_location(Bucket=bucket.name)['LocationConstraint']

    print(tabulate([['Bucket name','Creation Date','Location','Size','Number of objects','Total Cost'], \
        [bucket.name,bucket.creation_date,location,size(bucket_size),len(obj_dict)," ".join([unit,amount])]],headers='firstrow'))
    
	# List objects within the bucket and their details
    print('\nObjects:')
    print(tabulate(sorted(obj_dict.values(), key=operator.itemgetter('Class')),headers='keys'))
	
if __name__ == '__main__':

    if len(sys.argv) > 1:
        list_all_buckets(s3resource.Bucket(sys.argv[1]))
    else:
    	allbuckets = [bucket for bucket in s3resource.buckets.all()]
    	for bucket in allbuckets:
            list_all_buckets(bucket)
