""" Lambda function - terminate ec2 """
import boto3

def cloud_control_state_action_ec2(event, context):
    """ Lambda function - terminate ec2 """

    ec2 = boto3.resource('ec2')
    ec2_client = boto3.client('ec2')
    if event["body"]["InstanceName"] == "all":
        ec2_filter = [
            {
                'Name': 'instance-state-name',
                'Values': ['running', 'stopped', 'stopping']
            }
        ]
        instances = ec2.instances.filter(Filters=ec2_filter)
        instances_to_terminate = [instance.id for instance in instances]
        if len(instances_to_terminate) > 0:
            #perform the shutdown
            ec2.instances.filter(
                InstanceIds=instances_to_terminate).terminate()
            msg = "All instances were terminated!"
            return {"msg": msg}
        msg = "Nothing to terminate!"
        return {"msg": msg}
    else:
        response = ec2_client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': [event["body"]["InstanceName"]]
                }
            ]
        )
        instance_list = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_list.append(instance['InstanceId'])
        if not instance_list:
            msg = "I cannot find the instance with name {}.".format(
                event["body"]["InstanceName"]
            )
            return {"msg": msg}
        temp_msg = "I found instance {}. ".format(event["body"]["InstanceName"])
        ec2.instances.filter(
            InstanceIds=instance_list).terminate()
        msg = temp_msg + "Terminating."
        return {"msg": msg}
