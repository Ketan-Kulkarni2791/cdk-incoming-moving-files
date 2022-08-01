"""Code for generation and deployment of s3 resources."""
import imp
from typing import Dict, Any, List
from aws_cdk import core
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms
from aws_cdk.core import Stack
from aws_cdk import aws_s3 as s3
from aws_cdk.core import Duration


class S3Construct:
    """Class with static methods that are used to build and deploy s3."""
    
    @staticmethod
    def create_bucket(
        stack: Stack,
        bucket_id: str,
        bucket_name: str,
        bucket_desc: str,
        dest_bucket_arn: str,
        aws_account: str
        ) -> s3.Bucket:
        """Creates an encrypted bucket."""
        bucket_metrics = s3.BucketMetrics(
            id=f"erm-{bucket_name}"
        )
        
        lifecycle_rule = s3.LifecycleRule(
            abort_incomplete_multipart_upload_after=Duration.days(1),
            enabled=True,
            noncurrent_version_expiration=Duration.days(1)
        )
        
        ga_bucket = s3.Bucket(
            scope=stack,
            id=bucket_id,
            access_control=s3.BucketAccessControl.PUBLIC_READ_WRITE,
            public_read_access=True,
            # block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            bucket_name=bucket_name,
            versioned=True,
            metrics=[bucket_metrics],
            lifecycle_rules=[lifecycle_rule]
        )
        
        return ga_bucket
    
    
    @staticmethod
    def get_s3_object_policy(s3_bucket_arns: str) -> iam.PolicyStatement:
        """Returns policy statement for reading and writing S3 objects."""
        policy_statement = iam.PolicyStatement()
        policy_statement.effect = iam.Effect.ALLOW
        policy_statement.add_actions("s3:DeleteObject*")
        policy_statement.add_actions("s3:GetObject*")
        policy_statement.add_actions("s3:PutObject*")
        # policy_statement.add_actions("s3:ReplicateTags")
        policy_statement.add_actions("s3:ListBucket")
        policy_statement.add_actions("s3:GetBucketLocation")
        policy_statement.add_actions("s3:AbortMultipartUpload")
        policy_statement.add_actions("s3:ListBucketMultipartUploads")
        policy_statement.add_actions("s3:ListMultipartUploadParts")
        policy_statement.add_actions("s3:GetBucket*")
        policy_statement.add_resources(f"{s3_bucket_arns}")
        policy_statement.add_resources(f"{s3_bucket_arns}/*")
        return policy_statement
    
    
    @staticmethod
    def get_s3_bucket_policy(s3_bucket_arns: str) -> iam.PolicyStatement:
        """Returns policy statement for reading from S3 bucket."""
        policy_statement = iam.PolicyStatement()
        policy_statement.effect = iam.Effect.ALLOW
        policy_statement.add_actions("s3:GetBucket*")
        policy_statement.add_actions("s3:PutBucket")
        policy_statement.add_actions("s3:ListBucket")
        policy_statement.add_actions("s3:GetBucketLocation")
        policy_statement.add_actions("s3:GetObject")
        policy_statement.add_resources(s3_bucket_arns)
        return policy_statement