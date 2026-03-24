import logging
import time

import requests
from airflow.exceptions import AirflowException

from ml_pipeline.settings import settings

logger = logging.getLogger(__name__)


def poll_github_ci():
    """Poll GitHub Actions for the latest CI run status."""
    api_url = f"https://api.github.com/repos/{settings.github_repo}/actions/runs"
    headers = {
        "Authorization": f"Bearer {settings.github_pat}",
        "Accept": "application/vnd.github.v3+json",
    }
    params = {"branch": settings.branch_name, "status": "completed", "per_page": 1}

    logger.info("Polling GitHub Actions for %s...", settings.github_repo)
    for _ in range(20):
        try:
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            if not data["workflow_runs"]:
                logger.info("No workflow runs found yet.")
                time.sleep(30)
                continue

            latest_run = data["workflow_runs"][0]
            conclusion = latest_run["conclusion"]
            logger.info("Latest Run Conclusion: %s", conclusion)

            if conclusion == "success":
                logger.info("CI Passed!")
                return True
            elif conclusion == "failure":
                raise AirflowException("Latest CI run failed!")
        except requests.RequestException as e:
            logger.exception("Polling error: %s", e)
            time.sleep(30)

    raise AirflowException("Timed out waiting for GitHub CI.")
