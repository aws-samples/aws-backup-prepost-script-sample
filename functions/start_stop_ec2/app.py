import json
import datetime
import boto3
import logging

log = logging.getLogger()
log.setLevel(logging.INFO)
ec2_client = boto3.client('ec2')

def lambda_handler(event, context):
    
    final_event =  event['event']
    workflow_log = event['event']['Workflowlog']
    
    instance_ids = []
    for instance in workflow_log:
        instance_ids.append(instance['InstanceId'])
    
    if event['desiredState'] == 'stop':
        response = ec2_client.stop_instances(InstanceIds=instance_ids)
    elif event['desiredState'] == 'start':
        response = ec2_client.start_instances(InstanceIds=instance_ids)
    
    response = ec2_client.describe_instances(InstanceIds=instance_ids)
    
    instance_status = {}
    
    for i in response['Reservations']:
        instance_id = i['Instances'][0]['InstanceId']
        status = i['Instances'][0]['State']['Name']
        instance_status[instance_id] = status
        
    print(instance_status)
    
    
    for instance in workflow_log:
        status = instance_status[instance['InstanceId']]
        if event['desiredState'] == 'stop' or event['desiredState'] == 'stopped':
            instance.update(StopEc2InstanceStatus=status)
        elif event['desiredState'] == 'start' or event['desiredState'] == 'running':
            instance.update(StartEc2InstanceStatus=status)
            
        
    if event['desiredState'] == 'stopped':
        for status in instance_status.values():
            if status != 'stopped':
                final_event.update(InstanceDesiredState='stopping')
                return final_event
        final_event.update(InstanceDesiredState='stopped')
    elif event['desiredState'] == 'running':
        for status in instance_status.values():
            if status != 'running':
                final_event.update(InstanceDesiredState='pending')
                return final_event
        final_event.update(InstanceDesiredState='running')
    
    final_event.update(EndTime=str(datetime.datetime.now()))
    return final_event
