import copy
import json
import datetime
import boto3
import logging

log = logging.getLogger()
log.setLevel(logging.INFO)
ssm_client = boto3.client('ssm')

def lambda_handler(e, context):
    
    log.info(e)
    
    current_step = e["currentStep"]
    event = e["event"]
    run_command_details = event['RemoteRunCommandDetails']
    workflow_log = event['Workflowlog']
    
    if current_step == "CheckPreBackupScriptStatus":
        script_execution = run_command_details['PreBackupScriptDetails']['PreBackupScriptExecution']
        script_execution, workflow_log = checkAndUpdateStatus(script_execution, workflow_log, current_step)
    elif current_step == "CheckPostBackupScriptStatus":
        script_execution = run_command_details['PostBackupScriptDetails']['PostBackupScriptExecution']
        script_execution, workflow_log = checkAndUpdateStatus(script_execution, workflow_log, current_step)
    event.update(Workflowlog=workflow_log)
    event.update(EndTime=str(datetime.datetime.now()))

    return event

def checkAndUpdateStatus(script_execution_event, workflow_log, current_step):
    log.info("checking " + current_step)
    response = ssm_client.list_command_invocations(
        CommandId = script_execution_event['CommandId']
    )

    log.info(response)

    for ci in response['CommandInvocations']:
        for instance in workflow_log:
            if ci['InstanceId'] == instance['InstanceId']:
                print(instance)
                if current_step == 'CheckPreBackupScriptStatus':
                    instance['PreBackupScriptStatus'] = ci['Status']
                else:
                    instance['PostBackupScriptStatus'] = ci['Status']
        
    for instance in workflow_log:
        # if any of the instance state is still pending return final state as pending
        if current_step == 'CheckPreBackupScriptStatus':
            if instance['PreBackupScriptStatus'] == 'Pending':
                script_execution_event.update(Status='Pending')
                return script_execution_event, workflow_log
        elif current_step == 'CheckPostBackupScriptStatus':
            if instance['PostBackupScriptStatus'] == 'Pending':
                script_execution_event.update(Status='Pending')
                return script_execution_event, workflow_log
    script_execution_event.update(Status='Success')
    return script_execution_event, workflow_log