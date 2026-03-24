from pydantic import Field
from pydantic_settings import BaseSettings


class PipelineSettings(BaseSettings):
    """Validated at DAG parse time -- missing required vars cause a visible DAG import error."""

    github_repo: str = Field(alias="GITHUB_REPO")
    github_pat: str = Field(alias="GITHUB_PAT")
    branch_name: str = Field(default="main", alias="BRANCH_NAME")

    key_pair_name: str = Field(alias="KEY_PAIR_NAME")
    ami_id: str = Field(default="ami-00ac45f3035ff009e", alias="AMI_ID")
    security_group_id: str = Field(alias="SECURITY_GROUP_ID")
    instance_type: str = Field(default="t3.small", alias="INSTANCE_TYPE")
    aws_access_key_id: str = Field(alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(alias="AWS_SECRET_ACCESS_KEY")
    aws_default_region: str = Field(default="eu-west-3", alias="AWS_DEFAULT_REGION")

    mlflow_tracking_uri: str = Field(alias="MLFLOW_TRACKING_URI")
    mlflow_experiment_name: str = Field(default="california_housing", alias="MLFLOW_EXPERIMENT_NAME")

    ssh_private_key_content: str = Field(alias="SSH_PRIVATE_KEY_CONTENT")

    model_config = {"populate_by_name": True}


settings = PipelineSettings()
