#!/usr/bin/env python3
import os
from configparser import ConfigParser, ExtendedInterpolation
from aws_cdk import core

from cdk_move_incoming_files.cdk_move_incoming_files_stack import CdkMoveIncomingFilesStack


def main() -> None:
    """main.py method that the cdk will execute."""
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read("./config.ini")
    app = core.App()
    env = app.node.try_get_context("env")
    
    CdkMoveIncomingFilesStack(
        env_var=env,
        scope=app,
        app_id=config['global']['app-id'],
        config=config,
        env={
            "region": config['global']["region"],
            "account": config['global']['awsAccount']
        }
    )
    app.synth()
    

main()