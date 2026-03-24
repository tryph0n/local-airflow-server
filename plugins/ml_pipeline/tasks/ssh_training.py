import io
import logging
import time

import paramiko
from airflow.exceptions import AirflowException, AirflowFailException

from ml_pipeline.settings import settings

logger = logging.getLogger(__name__)


def run_training(public_ip):
    """Connect to EC2 via SSH and execute the MLflow training run."""
    if not public_ip:
        raise AirflowFailException("No public IP received.")

    logger.info("Connecting to %s...", public_ip)

    ssh_key = paramiko.RSAKey.from_private_key(io.StringIO(settings.ssh_private_key_content))
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        for i in range(10):
            try:
                ssh.connect(public_ip, username="ubuntu", pkey=ssh_key, timeout=10)
                break
            except (paramiko.SSHException, OSError) as e:
                logger.warning("Waiting for SSH... (%s)", e)
                time.sleep(10)
        else:
            raise AirflowException(
                f"Failed to establish SSH connection to {public_ip} after 10 attempts"
            )

        logger.info("Waiting for MLflow installation to be usable...")

        wait_cmd = """
        for i in {1..60}; do
            if python3 -c "import mlflow" > /dev/null 2>&1; then
                echo "Python found MLflow!"
                exit 0
            fi
            echo "Waiting for library..."
            sleep 5
        done
        echo "Timed out waiting for MLflow lib"
        exit 1
        """

        stdin, stdout, stderr = ssh.exec_command(wait_cmd)
        if stdout.channel.recv_exit_status() != 0:
            error_output = stderr.read().decode()
            logger.error("Environment setup stderr: %s", error_output)
            raise AirflowException("Environment Setup Failed")

        logger.info("Reading user data debug log...")
        stdin, stdout, stderr = ssh.exec_command("cat /var/log/user-data-debug.log")
        logger.info(stdout.read().decode())

        cmd = f"""
            export MLFLOW_TRACKING_URI={settings.mlflow_tracking_uri}
            export MLFLOW_EXPERIMENT_NAME={settings.mlflow_experiment_name}
            export AWS_ACCESS_KEY_ID={settings.aws_access_key_id}
            export AWS_SECRET_ACCESS_KEY={settings.aws_secret_access_key}
            export AWS_DEFAULT_REGION={settings.aws_default_region}

            echo "Verifying MLflow installation:"
            which mlflow

            echo "Starting MLflow Run..."
            python3 -m mlflow run https://github.com/{settings.github_repo} \
                --version {settings.branch_name} \
                --build-image
        """

        stdin, stdout, stderr = ssh.exec_command(cmd)

        for line in iter(stdout.readline, ""):
            logger.info(line.rstrip())

        if stdout.channel.recv_exit_status() != 0:
            logger.error("REMOTE SCRIPT FAILED. Reading user_data log...")
            _, log_out, _ = ssh.exec_command("cat /var/log/user-data.log")
            logger.error("User data log: %s", log_out.read().decode())

            error_output = stderr.read().decode()
            logger.error("STDERR: %s", error_output)
            raise AirflowException("Training Failed")

    finally:
        ssh.close()
