"""
s3_fetch.py

Utilities for downloading the GradCafe dataset from S3 into a local
SageMaker workspace using boto3.
"""

from __future__ import annotations

from pathlib import Path

import boto3


def download_applicant_data(
    bucket_name: str,
    object_key: str,
    output_path: Path,
) -> None:
    """
    Download the GradCafe applicant dataset from an S3 bucket.

    The file stored in S3 (applicant_data.json) is downloaded and saved
    locally inside the SageMaker workspace as applicant_data_SM.json.

    Args:
        bucket_name:
            Name of the S3 bucket containing the dataset.

        object_key:
            Object key of the dataset inside the bucket.

        output_path:
            Local filesystem path where the downloaded file should be saved.
    """

    s3_client = boto3.client("s3")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    s3_client.download_file(
        bucket_name,
        object_key,
        str(output_path),
    )

    print(f"Downloaded s3://{bucket_name}/{object_key} -> {output_path}")
