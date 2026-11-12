#!/usr/bin/env python3
"""
s3_security_auditor.py
EN: Audits AWS S3 buckets for Public Access Block, Server-Side Encryption (SSE), and Versioning.
PT: Audita buckets AWS S3 verificando bloqueio de acesso público, criptografia (SSE) e versionamento.
"""

import argparse
import json
from datetime import datetime, timezone
from typing import Dict, List
import boto3
from botocore.exceptions import ClientError


def check_public_access_block(s3_client, bucket_name: str) -> bool:
    """Returns True if all four S3 Public Access Block settings are enabled."""
    try:
        resp = s3_client.get_public_access_block(Bucket=bucket_name)
        cfg = resp.get("PublicAccessBlockConfiguration", {})
        return all(
            [
                cfg.get("BlockPublicAcls", False),
                cfg.get("IgnorePublicAcls", False),
                cfg.get("BlockPublicPolicy", False),
                cfg.get("RestrictPublicBuckets", False),
            ]
        )
    except ClientError:
        return False


def check_encryption(s3_client, bucket_name: str) -> str:
    """Returns the default encryption algorithm (e.g., AES256, aws:kms) or 'DISABLED'."""
    try:
        resp = s3_client.get_bucket_encryption(Bucket=bucket_name)
        rules = resp.get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
        if rules:
            return rules[0].get("ApplyServerSideEncryptionByDefault", {}).get("SSEAlgorithm", "ENABLED")
        return "DISABLED"
    except ClientError:
        return "DISABLED"


def check_versioning(s3_client, bucket_name: str) -> str:
    """Returns bucket versioning status ('Enabled' or 'Suspended/Disabled')."""
    try:
        resp = s3_client.get_bucket_versioning(Bucket=bucket_name)
        return resp.get("Status", "Disabled")
    except ClientError:
        return "Unknown"


def audit_all_buckets() -> List[Dict[str, object]]:
    s3 = boto3.client("s3")
    buckets = s3.list_buckets().get("Buckets", [])
    findings: List[Dict[str, object]] = []

    for b in buckets:
        name = b["Name"]
        pab_enabled = check_public_access_block(s3, name)
        encryption = check_encryption(s3, name)
        versioning = check_versioning(s3, name)
        compliant = pab_enabled and (encryption != "DISABLED")

        findings.append(
            {
                "bucket_name": name,
                "public_access_blocked": pab_enabled,
                "default_encryption": encryption,
                "versioning": versioning,
                "status": "COMPLIANT" if compliant else "NON_COMPLIANT",
            }
        )
        print(
            f"[{findings[-1]['status']:<13}] Bucket: {name:<32} | "
            f"PublicBlock: {str(pab_enabled):<5} | SSE: {encryption:<8} | Versioning: {versioning}"
        )

    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description="AWS S3 Security Posture Auditor")
    parser.add_argument("--output", help="Optional file path to export JSON audit report")
    args = parser.parse_args()

    print("==========================================================================")
    print("  AWS S3 SECURITY & COMPLIANCE AUDITOR")
    print("==========================================================================")
    results = audit_all_buckets()

    if args.output:
        report = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "total_buckets": len(results),
            "non_compliant_count": sum(1 for r in results if r["status"] == "NON_COMPLIANT"),
            "buckets": results,
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\n[OK] Audit report exported to {args.output}")


if __name__ == "__main__":
    main()
