"""Code for generating the step resources.
This is for creating the various tasks, retry, error
and states that are involved."""

from email import message
from typing import Dict, Any, List
from aws_cdk import aws_iam as iam
from aws_cdk import aws_sns as sns
from aws_cdk.aws_lambda import Function
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks
from aws_cdk.core import Stack, Duration

class StepFunctionConstruct:
    """Class has methods to create a step function."""
    
    @staticmethod
    def create_step_function(
        stack: Stack,
        env: str,
        config: dict,
        role: iam.Role,
        state_machine_name: str,
        moving_incoming_files: Function
        ) -> sfn.StateMachine:
        """Create step Function."""
        
        project_id_short = config['global']['source-id-short']
        
        # Moving Incoming Files Lambda Task
        moving_incoming_files_task = StepFunctionConstruct.create_lambda_task(
            task_lambda=moving_incoming_files,
            stack=stack,
            task_def="Moving Incoming Files Lambda",
            result_key="$.moving_files_output")
        
        definition = StepFunctionConstruct.create_step_function_definition(
            stack=stack,
            moving_incoming_files_task=moving_incoming_files_task
        )
        
        state_machine = sfn.StateMachine(
            scope=stack,
            id=f"{config['global']['app-name']}-stateMachine-Id",
            state_machine_name=state_machine_name,
            definition=definition,
            role=role
        )
        
        return state_machine
       
        
    @staticmethod
    def create_lambda_task(stack: Stack, task_def: str, task_lambda: Function,
                           result_key: str = '$') -> sfn.Task:
        """Create Lambda Task."""
        lambda_task = sfn.Task(
            scope=stack,
            id=task_def,
            task=aws_stepfunctions_tasks.InvokeFunction(task_lambda),
            result_path=result_key
        )
        return lambda_task
    
    
    @staticmethod
    def create_step_function_definition(
        stack: Stack,
        moving_incoming_files_task) -> sfn.Chain:
        """Create Step Function Definition."""
        
        exec_param = {"Execution.$": "$$.Execution.Id"}
        start_state = sfn.Pass(
            scope=stack,
            id="StartState",
            result_path="$.Execution",
            parameters=exec_param
        )
        success = sfn.Succeed(
            scope=stack,
            id="Moving Files Step Function Execution complete."
        )
        
        definition = sfn.Chain.start(
            state=start_state
        ).next(
            next=moving_incoming_files_task
        ).next(
            next=success
        )
        return definition
    
    
    @staticmethod
    def get_sfn_lambda_invoke_job_policy_statement(
        config: dict, env: str) -> iam.PolicyStatement:
        """Returns policy statement lambdas used for managing SFN resources and components."""
        policy_statement = iam.PolicyStatement()
        policy_statement.effect = iam.Effect.ALLOW
        policy_statement.add_actions("lambda:InvokeFunction")
        policy_statement.add_resources(config['global']['lambdaFunctionArnBase'])
        return policy_statement