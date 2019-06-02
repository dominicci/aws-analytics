#!/usr/bin/python

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

# function for retrieving object details within each bucket value passed
def retrieve_objects(bucket):
    bucket_size = 0
    obj_dict = {}
	
    # loop through object contents to retrieve details
    for obj in bucket.objects.all():

        obj_name = obj.key
        obj_age = now - obj.last_modified.replace(tzinfo=None)
        obj_mod = obj.last_modified.replace(tzinfo=None)
        obj_class = obj.storage_class
        more = obj.Object()
        obj_size = more.content_length

        bucket_size += obj_size
	
	# ignore folders which are considered objects in AWS from object tracking
        if obj_name.endswith('/'):
            pass

        else:
            obj_dict[obj_name] = {'Name': obj_name, 'Last Modified': obj_mod, \
                'Size': size(obj_size), 'Age in Days': obj_age.days, 'Class': obj_class}

    return obj_dict, bucket_size

# function to estimate costs for each S3 bucket using Cost Explorer
def estimate_s3_costs():
    start = (now - timedelta(days=30)).strftime('%Y-%m-%d')
    end = now.strftime('%Y-%m-%d')

    results = []

    token = None

    # filter results required for estimating service costs
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

# function for listing buckets and content details
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
    # try to grab bucket name passed in env var to filter details only for that bucket
    if len(sys.argv) > 1:
        try:
            list_all_buckets(s3resource.Bucket(sys.argv[1]))
        except Exception as e:
            print('No Such bucket!')
    else:
	# if no bucket passed in env var, this will list all bucket resources
    	allbuckets = [bucket for bucket in s3resource.buckets.all()]
    	for bucket in allbuckets:
            list_all_buckets(bucket)
