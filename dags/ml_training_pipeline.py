from datetime import datetime, timedelta

from airflow.sdk import task
from airflow.models.dag import DAG
from airflow.providers.amazon.aws.operators.ec2 import (
    EC2CreateInstanceOperator,
    EC2TerminateInstanceOperator,
)
from airflow.task.trigger_rule import TriggerRule

from ml_pipeline.settings import settings
from ml_pipeline.callbacks import on_failure_callback, on_retry_callback
from ml_pipeline.user_data import USER_DATA_SCRIPT
from ml_pipeline.tasks.github import poll_github_ci
from ml_pipeline.tasks.ec2 import check_instance_status, get_instance_public_ip
from ml_pipeline.tasks.ssh_training import run_training

DAG_ID = "github_ec2_ml_training"
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 3,
    "retry_delay": timedelta(minutes=1),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=15),
    "execution_timeout": timedelta(hours=1),
    "on_failure_callback": on_failure_callback,
    "on_retry_callback": on_retry_callback,
}

with DAG(
    dag_id=DAG_ID,
    schedule=None,
    default_args=default_args,
    catchup=False,
    max_active_runs=1,
    tags=["github", "ec2", "ml-training"],
) as dag:

    @task(execution_timeout=timedelta(minutes=30))
    def wait_for_github_ci():
        return poll_github_ci()

    @task
    def check_ec2_status(instance_ids):
        return check_instance_status(instance_ids)

    @task
    def get_public_ip(instance_id):
        return get_instance_public_ip(instance_id)

    @task(execution_timeout=timedelta(hours=2))
    def run_training_via_ssh(public_ip):
        return run_training(public_ip)

    create_ec2 = EC2CreateInstanceOperator(
        task_id="create_ec2_instance",
        region_name=settings.aws_default_region,
        image_id=settings.ami_id,
        max_count=1,
        min_count=1,
        config={
            "InstanceType": settings.instance_type,
            "KeyName": settings.key_pair_name,
            "SecurityGroupIds": [settings.security_group_id],
            "UserData": USER_DATA_SCRIPT,
            "InstanceInitiatedShutdownBehavior": "terminate",
            "TagSpecifications": [
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Name", "Value": "Airflow-Trainer"}],
                }
            ],
        },
        wait_for_completion=True,
        retries=0,
    )

    terminate_ec2 = EC2TerminateInstanceOperator(
        task_id="terminate_ec2_instance",
        region_name=settings.aws_default_region,
        instance_ids=[
            "{{ task_instance.xcom_pull(task_ids='create_ec2_instance')[0] }}"
        ],
        trigger_rule=TriggerRule.ALL_DONE,
    )

    github_signal = wait_for_github_ci()
    validated_instance_id = check_ec2_status(create_ec2.output)
    public_ip = get_public_ip(validated_instance_id)
    training_output = run_training_via_ssh(public_ip)

    github_signal >> create_ec2
    create_ec2 >> validated_instance_id >> public_ip >> training_output >> terminate_ec2
