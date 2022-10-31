import json
import datetime
import boto3
import logging

log = logging.getLogger()
log.setLevel(logging.INFO)
ec2_client = boto3.client('ec2')
ssm_client = boto3.client('ssm')

'''
aws ssm send-command 
--document-name "AWS-RunRemoteScript" 
--document-version "1" 
--targets '[{"Key":"tag:pre-backup","Values":["true"]}]' 
--parameters '{"sourceType":["S3"],"sourceInfo":["{\"path\":\"https://ssm-backup-scripts.s3.amazonaws.com/pre-backup.py\"}"],"commandLine":["pre-backup.py"],"workingDirectory":[""],"executionTimeout":["3600"]}'
--timeout-seconds 600 
--max-concurrency "50" 
--max-errors "0" 
--output-s3-bucket-name "ssm-backup-logs" 
--region us-east-1
'''

def lambda_handler(e, context):

    log.info(e)
    
    current_step = e["currentStep"]
    event = e["event"]
    run_command_details = event['RemoteRunCommandDetails']
    
    execution_details = {}
    
    if current_step == 'RunPreBackupScript':
        log.info('running pre backup script')
        execution_details = run_command_details['PreBackupScriptDetails']
        response = send_command(event, execution_details)
        # Get RemoteRunCommandDetails and make pre-script execution API call
        # InstnaceIds
        pre_backup_details = {
            'CommandId': response['Command']['CommandId'],
            'Status': response['Command']['Status']
        }
        execution_details.update(PreBackupScriptExecution=pre_backup_details)
        
    elif current_step == 'RunPostBackupScript':
        log.info('running post backup script')
        execution_details = run_command_details['PostBackupScriptDetails']
        response = send_command(event, execution_details)
        # Get RemoteRunCommandDetails and make post-script execution API call
        post_backup_details = {
            'CommandId': response['Command']['CommandId'],
            'Status': response['Command']['Status']
        }
        execution_details.update(PostBackupScriptExecution=post_backup_details)
                    
    event.update(RemoteRunCommandDetails=run_command_details)
    event.update(EndTime=str(datetime.datetime.now()))
    
    return event

def send_command(event, execution_details):
    log.info('running send command')
    return ssm_client.send_command(
        Targets=[
            {
                'Key': 'tag:' + event['TargetEC2TagKey'],
                'Values': [ event['TargetEC2TagValue'] ]
            }
        ],
        DocumentName='AWS-RunRemoteScript',
        DocumentVersion='1',
        TimeoutSeconds=execution_details['TimeoutInSeconds'],
        Parameters={
            "sourceType": ["S3"],
            "sourceInfo": ["{\"path\":\"" + execution_details['SourceS3Path'] + "\"}"],
            "commandLine": [ execution_details["CommandToRun"] ],
            "workingDirectory": [""],
            "executionTimeout": ["3600"]
        },
        # OutputS3Region=execution_details['OutputS3Region'],
        OutputS3BucketName=execution_details['OutputS3BucketName'],
        OutputS3KeyPrefix=execution_details['OutputS3KeyPrefix'],
        MaxConcurrency='50',
        MaxErrors='0'
    )