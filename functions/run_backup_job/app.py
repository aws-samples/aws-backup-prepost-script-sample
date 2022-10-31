import json
import boto3
import datetime

backup_client = boto3.client('backup')

def start_backup_job(event):
    # Starting Backup Job
    response = backup_client.start_backup_job(
        BackupVaultName=event['BackupVaultName'],
        ResourceArn=event['ResourceArn'],
        IamRoleArn=event['IamRoleArn'],
        # IdempotencyToken='string',
        # StartWindowMinutes=123,
        # CompleteWindowMinutes=123,
        # Lifecycle={
        #     'MoveToColdStorageAfterDays': 123,
        #     'DeleteAfterDays': 123
        # },
        # RecoveryPointTags={
        #     'string': 'string'
        # },
        # BackupOptions={
        #     'string': 'string'
        # }
    )
    
    event.update(BackupJobId=response['BackupJobId'])
    event.update(Status='in-progress')
    
    return event
     

def lambda_handler(event, context):
    # TODO implement
    print(json.dumps(event))
    
    result = start_backup_job(event)
    return result
