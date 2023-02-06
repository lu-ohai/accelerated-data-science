#!/usr/bin/env python
# -*- coding: utf-8 -*--

# Copyright (c) 2021, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from tests.unitary.default_setup.jobs.test_jobs_base import DataScienceJobPayloadTest
from ads.jobs import ContainerRuntime, infrastructure
from ads.jobs.builders.infrastructure.dsc_job import DSCJob
from ads.jobs.builders.infrastructure.dsc_job_runtime import (
    DataScienceJobRuntimeManager,
    ContainerRuntimeHandler,
)


class ContainerRuntimeTestCase(DataScienceJobPayloadTest):
    # The test cases will check the payload generated by the ADS API
    # The container runtime is expect to modify only the environmentVariables in the payload.
    def test_create_container_job(self):
        expected_env_var = {
            "CONTAINER_CUSTOM_IMAGE": "iad.ocir.io/ociodscdev/qq-repo/ubuntu",
            "CONTAINER_ENTRYPOINT": "/bin/sh",
            "CONTAINER_CMD": "-c,echo Hello World",
            "MY_ENV": "MY_VALUE",
        }

        # Use different ways to create the same runtime
        runtimes = [
            ContainerRuntime()
            .with_image(
                "iad.ocir.io/ociodscdev/qq-repo/ubuntu",
                entrypoint="/bin/sh",
                cmd="-c,echo Hello World",
            )
            .with_environment_variable(MY_ENV="MY_VALUE"),
            ContainerRuntime()
            .with_image("iad.ocir.io/ociodscdev/qq-repo/ubuntu")
            .with_cmd("-c,echo Hello World")
            .with_entrypoint("/bin/sh")
            .with_environment_variable(MY_ENV="MY_VALUE"),
            ContainerRuntime()
            .with_image("iad.ocir.io/ociodscdev/qq-repo/ubuntu")
            .with_cmd(["-c", "echo Hello World"])
            .with_entrypoint("/bin/sh")
            .with_environment_variable(MY_ENV="MY_VALUE"),
        ]

        for runtime in runtimes:
            self.assertEqual(runtime.entrypoint, "/bin/sh")
            self.assert_runtime_translation(runtime, expected_env_var)

    def test_container_runtime_extraction(self):
        ds_job = infrastructure.DataScienceJob.from_dsc_job(
            DSCJob(
                **{
                    "projectId": "ocid1.datascienceproject.oc1.iad.<unique_ocid>",
                    "compartmentId": "ocid1.compartment.oc1..<unique_ocid>",
                    "displayName": "<job_name>",
                    "jobConfigurationDetails": {
                        "jobType": "DEFAULT",
                        "commandLineArguments": "pos_arg1 pos_arg2 --key1 val1 --key2 val2",
                        "environmentVariables": {
                            ContainerRuntimeHandler.CONST_CONTAINER_IMAGE: "python",
                            ContainerRuntimeHandler.CONST_CONTAINER_ENTRYPOINT: "/bin/sh",
                            ContainerRuntimeHandler.CONST_CONTAINER_CMD: "-c,ls -l",
                            "KEY1": "VALUE1",
                            "KEY2": "VALUE2",
                            # Conda env var will be kept as env var for container runtime.
                            "CONDA_ENV_TYPE": "service",
                            "CONDA_ENV_SLUG": "mlcpuv1",
                        },
                        "maximumRuntimeInMinutes": 300,
                    },
                    "jobInfrastructureConfigurationDetails": {
                        "jobInfrastructureType": "STANDALONE",
                        "shapeName": "VM.Standard2.1",
                        "blockStorageSizeInGBs": "100",
                        "subnetId": "ocid1.subnet.oc1.iad.<unique_ocid>",
                    },
                }
            )
        )

        runtime = DataScienceJobRuntimeManager(ds_job).extract(ds_job.dsc_job)
        expected_runtime_spec = {
            "args": ["pos_arg1", "pos_arg2", "--key1", "val1", "--key2", "val2"],
            "image": "python",
            "cmd": ["-c", "ls -l"],
            "entrypoint": ["/bin/sh"],
            "env": [
                {"name": "KEY1", "value": "VALUE1"},
                {"name": "KEY2", "value": "VALUE2"},
                {"name": "CONDA_ENV_TYPE", "value": "service"},
                {"name": "CONDA_ENV_SLUG", "value": "mlcpuv1"},
            ],
            "maximumRuntimeInMinutes": 300,
        }
        self.assertIsInstance(runtime, ContainerRuntime)
        self.assertEqual(runtime.to_dict().get("spec"), expected_runtime_spec)
