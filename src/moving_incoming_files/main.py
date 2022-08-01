"""Runs as Incoming Data to S3 Transform Location Lambda.

Raises-
    error: lambda exception
Returns-
    [dict]:

"""
import boto3
import os
from datetime import datetime
import logging

logging.getLogger().setLevel(logging.INFO)

bucket_name = os.environ['bucket_name']
source_key = os.environ['processing_folder']
dest_key = os.environ['dataset_folder']


def incoming_data_mover(filedate):
    
    s3_client = boto3.client("s3")
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket_name)
    eventDate = datetime.strptime(filedate, "%Y-%m-%d")
    dd, mm, yyyy = str(eventDate.day).zfill(2), str(eventDate.month).zfill(2), str(eventDate.year)
    print(f"""{yyyy}-{mm}-{dd}""")
    final_source_key = f"{source_key}/yyyy={yyyy}/mm={mm}/dd={dd}"
    for bucket_object in bucket.objects.filter(Prefix=final_source_key):
        path, file = os.path.split(bucket_object.key)
        copy_source_object = {
            'Bucket': bucket_name, 'Key': f"""{path}/{file}"""
        }
        if file == "":
            continue
        else:
            s3_client.copy_object(CopySource=copy_source_object, Bucket=bucket_name,
                                  Key=f"""{dest_key}/yyyy={yyyy}/mm={mm}/dd={dd}/{file}""") 
            s3_client.delete_object(Bucket=bucket_name, Key=f"""{path}/{file}""")
    return "success"


def lambda_handler(event: dict, _context: dict) -> dict:
    """Main lambda handler for Incoming Data to S3 Transform Location Lambda."""
    
    # In case a correct event is encountered -------------------------------------------
    if event:
        # Create template and extract values from event --------------------------------
        logging.info("This is the event we received: %s", event)
        try:
            filedate = event['asof_date']
            incoming_data_mover(filedate)
            return {
                'asof_date': filedate
            }
        # In case an error is encountered even when a correct event is present ---------
        except Exception as error:
            logging.error("An error occurred: %s", error)
            raise error
    # In case no event is present ------------------------------------------------------
    else:
        logging.error("We couldn't find a suitable event. Exiting....")
        raise OSError("No event found")
    
    