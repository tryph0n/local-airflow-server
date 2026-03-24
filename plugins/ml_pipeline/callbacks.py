import logging

logger = logging.getLogger(__name__)


def on_failure_callback(context):
    ti = context["task_instance"]
    logger.error(
        "Task %s failed in DAG %s. Exception: %s. Log URL: %s",
        ti.task_id,
        ti.dag_id,
        context.get("exception"),
        ti.log_url,
    )


def on_retry_callback(context):
    ti = context["task_instance"]
    logger.warning(
        "Retrying task %s in DAG %s (attempt %s)",
        ti.task_id,
        ti.dag_id,
        ti.try_number,
    )
