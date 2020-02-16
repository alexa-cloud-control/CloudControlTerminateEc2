""" Lambda function - terminate ec2 """
import boto3
import json

def write_to_dynamo(context):
    """ Write data to DynamoDB table """
    dynamodb_resource = boto3.resource('dynamodb')
    dynamodb_client = boto3.client('dynamodb')
    # function env variable - to change
    context_table = dynamodb_resource.Table('alexa-cloudcontrol-context')
    for context_key, context_value in context.items():
        try:
            context_table.put_item(
                Item={
                    'Element': context_key,
                    'ElementValue': context_value
                }
            )
        except dynamodb_client.exceptions.ClientError as error:
            msg = "Something wrong with my table!"
            print(error)
            return {"msg": msg}
    return 0

def validate_with_dynamo(context):
    """ Read context from DynamoDB table """
    context_list=[
        'the-same',
        'same',
        'like-last-one',
        'like-last-1',
        'last-one',
        'last-1',
        'last',
        'previous',
        'previous-one',
        'previous-1',
        'like-before',
        'like-last-time'
    ]
    dynamodb_resource = boto3.resource('dynamodb')
    dynamodb_client = boto3.client('dynamodb')
    context_table = dynamodb_resource.Table('alexa-cloudcontrol-context')
    function_payload = {}
    # Check if context contains context_list. If yes, check dynamo if there is a value
    # for it. If no, throw error.
    for context_key, context_value in context.items():
        if context_value in context_list:
            try:
                response = context_table.get_item(
                    Key={
                        'Element': context_key
                    }
                )
                function_payload[context_key] = response['Item']['ElementValue']
            except dynamodb_client.exceptions.ClientError as error:
                msg = "I don't remember anything for {}".format(
                    context_key
                )
                print(error)
                return {"msg": msg}
            
        else:
            function_payload[context_key] = context_value
    json_payload = json.dumps(function_payload)
    return json_payload

def cloud_control_terminate_ec2(event, context):
    """ Lambda function - terminate ec2 """

    ec2 = boto3.resource('ec2')
    ec2_client = boto3.client('ec2')
    msg = ""
    validate_with_context_payload = {
        "LastInstanceName": event["body"]["InstanceName"]
    }
    response = {}
    response = validate_with_dynamo(validate_with_context_payload)
    payload_response = json.loads(response)
    validated_instance_name = payload_response["LastInstanceName"]
    if validated_instance_name == "all":
        ec2_filter = [
            {
                'Name': 'instance-state-name',
                'Values': ['running', 'stopped', 'stopping']
            }
        ]
        instances = ec2.instances.filter(Filters=ec2_filter)
        instances_to_terminate = [instance.id for instance in instances]
        if instances_to_terminate:
            #perform the shutdown
            ec2.instances.filter(
                InstanceIds=instances_to_terminate).terminate()
            msg = "All instances were terminated!"
            return {"msg": msg}
        msg = "Nothing to terminate!"
        return {"msg": msg}
    response = ec2_client.describe_instances(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [validated_instance_name]
            }
        ]
    )
    instance_list = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_list.append(instance['InstanceId'])
    if not instance_list:
        msg = "I cannot find the instance with name {}.".format(
            validated_instance_name
        )
        return {"msg": msg}
    temp_msg = "I found instance {}. ".format(validated_instance_name)
    ec2.instances.filter(
        InstanceIds=instance_list).terminate()
    msg = temp_msg + "Terminating."
    if validated_instance_name != "all":
        write_to_table_payload = {
            "LastInstanceName": validated_instance_name
        }
    write_to_dynamo(write_to_table_payload)
    return {"msg": msg}
