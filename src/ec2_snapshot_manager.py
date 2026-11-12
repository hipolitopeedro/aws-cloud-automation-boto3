#!/usr/bin/env python3
"""
ec2_snapshot_manager.py
EN: Automates EBS volume snapshot creation for tagged EC2 instances and rotates expired snapshots.
PT: Automatiza a criação de snapshots EBS para instâncias EC2 com tag de backup e remove snapshots expirados.
"""

import argparse
from datetime import datetime, timedelta, timezone
import boto3
from botocore.exceptions import ClientError


def create_snapshots(ec2_client, tag_key: str, tag_value: str, dry_run: bool) -> int:
    """Finds EC2 instances matching the backup tag and snapshots their attached EBS volumes."""
    paginator = ec2_client.get_paginator("describe_instances")
    filters = [
        {"Name": f"tag:{tag_key}", "Values": [tag_value]},
        {"Name": "instance-state-name", "Values": ["running", "stopped"]},
    ]

    created_count = 0
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")

    for page in paginator.paginate(Filters=filters):
        for reservation in page.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instance_id = instance["InstanceId"]
                instance_name = next(
                    (t["Value"] for t in instance.get("Tags", []) if t["Key"] == "Name"),
                    instance_id,
                )

                for mapping in instance.get("BlockDeviceMappings", []):
                    ebs = mapping.get("Ebs")
                    if not ebs:
                        continue
                    volume_id = ebs["VolumeId"]
                    description = f"AutoBackup_{instance_name}_{instance_id}_{volume_id}_{timestamp}"

                    print(f"[INFO] Creating snapshot for volume {volume_id} ({instance_name})...")
                    if dry_run:
                        print(f"[DRY-RUN] Would create snapshot: {description}")
                        created_count += 1
                        continue

                    try:
                        snap = ec2_client.create_snapshot(
                            VolumeId=volume_id,
                            Description=description,
                            TagSpecifications=[
                                {
                                    "ResourceType": "snapshot",
                                    "Tags": [
                                        {"Key": "Name", "Value": f"AutoBackup-{instance_name}"},
                                        {"Key": "CreatedBy", "Value": "AutomatedSnapshotManager"},
                                        {"Key": "SourceInstanceId", "Value": instance_id},
                                    ],
                                }
                            ],
                        )
                        print(f"[OK] Snapshot created: {snap['SnapshotId']}")
                        created_count += 1
                    except ClientError as exc:
                        print(f"[ERROR] Failed to snapshot {volume_id}: {exc}")

    return created_count


def cleanup_old_snapshots(ec2_client, retention_days: int, dry_run: bool) -> int:
    """Deletes snapshots tagged with CreatedBy=AutomatedSnapshotManager older than retention_days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    filters = [{"Name": "tag:CreatedBy", "Values": ["AutomatedSnapshotManager"]}]

    response = ec2_client.describe_snapshots(OwnerIds=["self"], Filters=filters)
    deleted_count = 0

    for snap in response.get("Snapshots", []):
        snap_id = snap["SnapshotId"]
        start_time = snap["StartTime"]

        if start_time < cutoff:
            age_days = (datetime.now(timezone.utc) - start_time).days
            print(f"[INFO] Snapshot {snap_id} is {age_days} days old (threshold: {retention_days}d).")
            if dry_run:
                print(f"[DRY-RUN] Would delete snapshot {snap_id}")
                deleted_count += 1
                continue

            try:
                ec2_client.delete_snapshot(SnapshotId=snap_id)
                print(f"[OK] Deleted expired snapshot {snap_id}")
                deleted_count += 1
            except ClientError as exc:
                print(f"[ERROR] Could not delete snapshot {snap_id}: {exc}")

    return deleted_count


def main() -> None:
    parser = argparse.ArgumentParser(description="AWS EC2 EBS Snapshot Lifecycle Manager")
    parser.add_argument("--region", default="us-east-1", help="AWS Region (default: us-east-1)")
    parser.add_argument("--tag-key", default="Backup", help="EC2 tag key to filter (default: Backup)")
    parser.add_argument("--tag-value", default="true", help="EC2 tag value to filter (default: true)")
    parser.add_argument("--retention-days", type=int, default=14, help="Snapshot retention in days (default: 14)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions without modifying AWS resources")
    args = parser.parse_args()

    ec2 = boto3.client("ec2", region_name=args.region)
    created = create_snapshots(ec2, args.tag_key, args.tag_value, args.dry_run)
    deleted = cleanup_old_snapshots(ec2, args.retention_days, args.dry_run)

    print(f"\n[SUMMARY] Snapshots created: {created} | Expired snapshots removed: {deleted}")


if __name__ == "__main__":
    main()
