import json
import datetime
import boto3
import logging

log = logging.getLogger()
log.setLevel(logging.INFO)

IN_PROGRESS_LIST = ["PENDING", "ABORTING", "RUNNING", "CREATED"]
BACKUP_STATE_ABORTED = "ABORTED"

backup_client = boto3.client('backup')

def fetch_overall_backup_status(event):
    states = []
    for backup_job in event['BackupDetails']:
        response = backup_client.describe_backup_job(
                        BackupJobId=backup_job['BackupJobId']) 
        state = response['State']
        backup_job.update(Status=state)
        states.append(state)
        
        event.update(EndTime=str(datetime.datetime.now()))
        update_workflowlog_status(backup_job['ResourceArn'], state, event['Workflowlog'])
        if 'StatusMessage' in response:
            backup_job.update(StatusMessage=response['StatusMessage'])
    if any(status in IN_PROGRESS_LIST for status in states):
        event.update(BackupJobsStatus='in-progress')
        return event
    if BACKUP_STATE_ABORTED in states:
        event.update(BackupJobsStatus='failed')
        return event
    
    event.update(BackupJobsStatus='complete')
    return event
        

def lambda_handler(event, context):
    log.info('checking backup status')
    log.info(json.dumps(event['BackupDetails']))
    
    result = fetch_overall_backup_status(event)
    
    return result


def update_workflowlog_status(instance_arn, status, workflow_log):
    instance_id = instance_arn.split("/")[1]
    instance = [x for x in workflow_log if x['InstanceId'] == instance_id][0]
    instance.update(BackupJobStatus=status)
