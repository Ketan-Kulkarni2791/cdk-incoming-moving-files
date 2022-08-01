"""Main python file_key for adding resources to the application stack."""
from typing import Dict, Any
from aws_cdk import (
    core,
    aws_lambda,
    aws_kms as kms,
    aws_s3 as s3,
    aws_iam as iam
)
from .kms_construct import KMSConstruct
from .iam_construct import IAMConstruct
from .s3_construct import S3Construct
from .lambda_construct import LambdaConstruct
from .stepfunction_construct import StepFunctionConstruct

class CdkMoveIncomingFilesStack(core.Stack):
    """Build the app stacks and its resources."""
    def __init__(self, env_var: str, scope: core.Construct, 
                 app_id: str, config: dict, **kwargs: Dict[str, Any]) -> None:
        """Creates the cloudformation templates for the projects."""
        super().__init__(scope, app_id, **kwargs)
        self.env_var = env_var
        self.config = config
        CdkMoveIncomingFilesStack.create_stack(self, self.env_var, config=config)
       
        
    @staticmethod
    def create_stack(stack: core.Stack, env: str, config: dict) -> None:
        """Create and add the resources to the application stack"""
        
        # KMS infra setup
        kms_pol_doc = IAMConstruct.get_kms_policy_document()
        
        kms_key = KMSConstruct.create_kms_key(
            stack=stack,
            config=config,
            env=env,
            policy_doc=kms_pol_doc
        )
        
        # IAM Role Setup
        stack_role = CdkMoveIncomingFilesStack.create_stack_role(
            config=config,
            env=env,
            stack=stack,
            kms_key=kms_key,
            destination_bucket_arn=config['global']['dr_bucket_arn'],
            source_bucket_arn=config['global']['bucket_arn'],
            destination_bucket_kms_Arn=config['global']['bucketDrKmsKeyArn'],
            source_bucket_kms_Arn=config['global']['bucketKmsKeyArn']
        )
        
        # S3 Bucket Infra Setup --------------------------------------------------
        s3_bucket = CdkMoveIncomingFilesStack.create_bucket(
            config=config,
            env=env,
            dest_bucket_arn=config['global']['bucket_arn'],
            aws_account=config['global']['awsAccount'],
            stack=stack
        )
        
        # Infra for Lambda function creation.
        lambdas = CdkMoveIncomingFilesStack.create_lambda_functions(
            stack=stack,
            config=config,
            env=env,
            kms_key=kms_key
        )
        
        # Moving Incoming Files Step Function Infra
        CdkMoveIncomingFilesStack.create_step_function(
            stack=stack,
            config=config,
            env=env,
            state_machine_name=f"{config['global']['app-name']}-actuals-stateMachine",
            lambdas=lambdas
        )
        
        
    @staticmethod
    def create_stack_role(
        config: dict,
        env: str,
        stack: core.Stack,
        kms_key: kms.Key
    ) -> iam.Role:
        """Create the IAM role."""
        
        stack_policy = IAMConstruct.create_managed_policy(
            stack=stack,
            env=env,
            config=config,
            policy_name="mainStack",
            statements=[
                KMSConstruct.get_kms_key_encrypt_decrypt_policy(
                    [kms_key.key_arn]
                ),
                S3Construct.get_s3_object_policy([config['global']['bucket_arn']]),
            ]
        )
        stack_role = IAMConstruct.create_role(
            stack=stack,
            env=env,
            config=config,
            role_name="mainStack",
            assumed_by=["s3", "lambda"]
        )
        stack_role.add_managed_policy(policy=stack_policy)
        return stack_role
        
        
        
    @staticmethod
    def create_bucket(
        config: dict,
        env: str,
        dest_bucket_arn: str,
        aws_account: str,
        stack: core.Stack) -> s3.Bucket:
        """Create an encrypted s3 bucket."""
        
        s3_bucket = S3Construct.create_bucket(
            stack=stack,
            bucket_id=f"moving-incoming-files-{config['global']['env']}",
            bucket_name=config['global']['bucket_name'],
            bucket_desc=f"for storing files for {config['global']['app-name']}",
            dest_bucket_arn=dest_bucket_arn,
            aws_account=aws_account
        )
        return s3_bucket
    
    
    @staticmethod
    def create_lambda_functions(
        stack: core.Stack,
        config: dict,
        env: str,
        kms_key: kms.Key) -> Dict[str, aws_lambda.Function]:
        """Create placeholder lambda function and roles."""
        
        lambdas = {}
        
        # Moving incoming files to S3 destination lambda.
        moving_incoming_files_policy = IAMConstruct.create_managed_policy(
            stack=stack,
            env=env,
            config=config,
            policy_name="moving_incoming_files",
            statements=[
                LambdaConstruct.get_cloudwatch_policy(
                    config['global']['moving_incoming_files_lambdaLogsArn']
                ),
                S3Construct.get_s3_object_policy(config['global']['bucket_arn']),
                S3Construct.get_s3_bucket_policy(config['global']['bucket_arn']),
                KMSConstruct.get_kms_key_encrypt_decrypt_policy([kms_key.key_arn])
            ]
        )
        moving_incoming_files_role = IAMConstruct.create_role(
            stack=stack,
            env=env,
            config=config,
            role_name="moving_incoming_files",
            assumed_by=["lambda", "s3"]   
        )
        moving_incoming_files_role.add_managed_policy(moving_incoming_files_policy)
        
        lambdas["moving_incoming_files_lambda"] = LambdaConstruct.create_lambda(
            stack=stack,
            env=env,
            config=config,
            lambda_name="moving_incoming_files_lambda",
            role=moving_incoming_files_role,
            duration=core.Duration.minutes(15)
        )
        
        return lambdas
    
    
    @staticmethod
    def create_step_function(
        stack: core.Stack,
        config: dict,
        env: str,
        state_machine_name: str,
        lambdas: Dict[str, aws_lambda.Function]) -> None:
        """Create Step Function and necessary IAM role with input lambdas."""
        
        state_machine_policy = IAMConstruct.create_managed_policy(
            stack=stack,
            env=env,
            config=config,
            policy_name="movingIncomingFilesStateMachine",
            statements=[
                StepFunctionConstruct.get_sfn_lambda_invoke_job_policy_statement(
                    config=config,
                    env=env
                )
            ]
        )
        
        state_machine_role = IAMConstruct.create_role(
            stack=stack,
            env=env,
            config=config,
            role_name="movingIncomingFilesStateMachine",
            assumed_by=['states']
        )
        state_machine_role.add_managed_policy(state_machine_policy)
        
        StepFunctionConstruct.create_step_function(
            stack=stack,
            env=env,
            config=config,
            role=state_machine_role,
            state_machine_name=state_machine_name,
            moving_incoming_files=lambdas["moving_incoming_files_lambda"]
        )
        