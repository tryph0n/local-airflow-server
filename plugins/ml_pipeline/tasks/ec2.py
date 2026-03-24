import logging

import boto3
from airflow.exceptions import AirflowFailException

from ml_pipeline.settings import settings

logger = logging.getLogger(__name__)


def check_instance_status(instance_ids):
    """Wait for EC2 instance to pass status checks and return the instance ID."""
    if not instance_ids:
        raise AirflowFailException("No instance IDs received from create_ec2_instance.")
    instance_id = instance_ids[0]
    client = boto3.client("ec2", region_name=settings.aws_default_region)
    logger.info("Waiting for instance %s to pass status checks...", instance_id)
    waiter = client.get_waiter("instance_status_ok")
    waiter.wait(InstanceIds=[instance_id])
    logger.info("Instance %s is ready.", instance_id)
    return instance_id


def get_instance_public_ip(instance_id):
    """Get the public IP address of an EC2 instance."""
    if not instance_id:
        raise AirflowFailException("No instance ID received.")
    ec2 = boto3.resource("ec2", region_name=settings.aws_default_region)
    instance = ec2.Instance(instance_id)
    public_ip = instance.public_ip_address
    logger.info("Instance %s public IP: %s", instance_id, public_ip)
    return public_ip
