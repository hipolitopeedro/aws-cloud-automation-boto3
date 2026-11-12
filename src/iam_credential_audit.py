#!/usr/bin/env python3
"""
iam_credential_audit.py
EN: Audits AWS IAM users for MFA enforcement and active Access Keys older than N days.
PT: Audita usuários AWS IAM verificando uso de MFA e chaves de acesso (Access Keys) antigas.
"""

import argparse
from datetime import datetime, timezone
import boto3


def audit_iam_users(max_key_age_days: int) -> None:
    iam = boto3.client("iam")
    paginator = iam.get_paginator("list_users")
    now = datetime.now(timezone.utc)

    print("==========================================================================")
    print(f"  AWS IAM SECURITY AUDIT (Max Access Key Age: {max_key_age_days} days)")
    print("==========================================================================")

    for page in paginator.paginate():
        for user in page.get("Users", []):
            username = user["UserName"]
            mfa_devices = iam.list_mfa_devices(UserName=username).get("MFADevices", [])
            has_mfa = len(mfa_devices) > 0

            keys = iam.list_access_keys(UserName=username).get("AccessKeyMetadata", [])
            active_old_keys = []
            for k in keys:
                if k["Status"] == "Active":
                    age_days = (now - k["CreateDate"]).days
                    if age_days >= max_key_age_days:
                        active_old_keys.append(f"{k['AccessKeyId']} ({age_days}d)")

            status = "OK" if (has_mfa and not active_old_keys) else "REVIEW_REQUIRED"
            old_keys_str = ", ".join(active_old_keys) if active_old_keys else "None"
            print(
                f"[{status:<15}] User: {username:<24} | MFA Enabled: {str(has_mfa):<5} | "
                f"Expired Active Keys: {old_keys_str}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="AWS IAM MFA & Access Key Rotation Auditor")
    parser.add_argument("--max-key-age-days", type=int, default=90, help="Max age in days for active IAM keys")
    args = parser.parse_args()
    audit_iam_users(args.max_key_age_days)


if __name__ == "__main__":
    main()
