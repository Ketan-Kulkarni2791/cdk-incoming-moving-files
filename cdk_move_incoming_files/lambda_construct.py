"""Code for generation and deploy lambda to AWS"""
import json
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda
from aws_cdk import aws_logs
from aws_cdk.core import Stack, Duration


class LambdaConstruct:
    """Class with static methods that are used to build and deploy lambdas."""
    
    @staticmethod
    def create_lambda(
        stack: Stack,
        env: str,
        config: dict,
        lambda_name: str,
        role: iam.Role,
        duration: Duration = None
    ) -> aws_lambda.Function:
        """Method called by construct for creating lambda."""
        
        env_vars = json.loads(config['global'][f"{lambda_name}Environment"])
        return LambdaConstruct.create_lambda_function(
            stack=stack,
            config=config,
            env=env,
            lambda_name=lambda_name,
            role=role,
            env_vars=env_vars,
            duration=duration
        )
        
        
    @staticmethod
    def create_lambda_function(
        stack: Stack,
        config: dict,
        env: str,
        lambda_name: str,
        role: iam.Role,
        env_vars: dict,
        duration: Duration) -> aws_lambda.Function:
        """Methods for generic lambda creation."""
        
        lambda_path = config['global'][f"{lambda_name}HndlrPath"]
        handler =  config['global'][f"{lambda_name}Hndlr"]
        function_id = f"{config['global']['app-name']}-{lambda_name}-Id"
        function_name = f"{config['global']['app-name']}-{lambda_name}"
        
        dict_props = {
            "function_name": function_name,
            "code": aws_lambda.Code.from_asset(path=lambda_path),
            "handler": handler,
            "runtime": aws_lambda.Runtime.PYTHON_3_8,
            "role": role,
            "environment": env_vars,
            "timeout": duration,
            "log_retention": aws_logs.RetentionDays.THREE_MONTHS
        }
        
        return aws_lambda.Function(scope=stack, id=function_id, **dict_props)
    
    
    @staticmethod
    def get_cloudwatch_policy(lambda_logs_arn: str) -> iam.PolicyStatement:
        """Returns policy statement for creating logs."""
        policy_statement = iam.PolicyStatement()
        policy_statement.effect = iam.Effect.ALLOW
        policy_statement.add_actions("cloudwatch:PutMetricData")
        policy_statement.add_actions("logs:CreateLogGroup")
        policy_statement.add_actions("logs:CreateLogStream")
        policy_statement.add_actions("logs:GetQueryResults")
        policy_statement.add_actions("logs:PutLogEvents")
        policy_statement.add_actions("logs:StartQuery")
        policy_statement.add_resources(lambda_logs_arn)
        return policy_statement