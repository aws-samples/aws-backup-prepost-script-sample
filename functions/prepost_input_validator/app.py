import copy
import datetime
import boto3
import logging

log = logging.getLogger()
log.setLevel(logging.INFO)
ec2_client = boto3.client('ec2')
session = boto3.session.Session()
current_region = session.region_name
current_account = boto3.client('sts').get_caller_identity()['Account']

def lambda_handler(event, context):
    
    log.info(event)
    
    pre_backup_required = False
    post_backup_required = False
    
    run_command_details = event['RemoteRunCommandDetails']
    
    if 'PreBackupScriptDetails' in run_command_details:
        log.info('Pre scirpt execution is required')
        pre_backup_required = True
    if 'PostBackupScriptDetails' in run_command_details:
        log.info('Post scirpt execution is required')
        post_backup_required = True
        
    event.update(RunPreBackupScript=pre_backup_required)
    event.update(RunPostBackupScript=post_backup_required)
    
    instances = get_ec2_instances(event)
    
    # build the back details
    backup_details = event['BackupDetails']
    backup_list = []
    for instance in instances:
        job = copy.deepcopy(backup_details)
        # TODO Fetch Arn here
        resource_arn = 'arn:aws:ec2:' + get_region(context) + ':' + get_account_id(context) + ':instance/' + instance
        job.update(ResourceArn=resource_arn)
        backup_list.append(job)
        event.update(BackupDetails=backup_list)

    # build workflow status
    workflowLog = []
    for instance in instances:
        workflowLog.append({
            "InstanceId": instance,
            "PreBackupScriptStatus":   "" if pre_backup_required else "skipped",
            "StopEc2InstanceStatus": "" if event["StartStopEC2Required"] else "skipped",
            "BackupJobStatus": "",
            "PostBackupScriptStatus": "" if post_backup_required else "skipped",
            "StartEc2InstanceStatus": "" if event["StartStopEC2Required"] else "skipped",
            "FailureMessage": ""
        })
    event.update(Workflowlog=workflowLog)
    event.update(StartTime=str(datetime.datetime.now()))

    log.info(event)
    
    return event


def get_ec2_instances(event):
    # Return list of instance-ids if available
    if 'TargetEC2Instances' in event:
        return event['TargetEC2Instances']
    # else fetch the instance-ids by tag
    filters =[
        {
            'Name':'tag:' + event['TargetEC2TagKey'],
            'Values': [ event['TargetEC2TagValue'] ]
        }
    ]
    
    describe_instances = ec2_client.describe_instances(Filters=filters,MaxResults=1000) # TODO handle pagination
    instances = []
    if len(describe_instances['Reservations']) > 0:
        for instance in describe_instances['Reservations']:
            instances.append(instance['Instances'][0]['InstanceId'])
    return instances

def get_account_id(context):
    return current_account

def get_region(context):
    return current_region