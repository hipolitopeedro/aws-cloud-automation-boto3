#!/usr/bin/env bash
# ==============================================================================
# Script: aws-cost-and-inventory.sh
# EN: Lists running EC2 instances, unattached EBS volumes, and unused Elastic IPs.
# PT: Lista instâncias EC2 ativas, volumes EBS órfãos e Elastic IPs não alocados.
# ==============================================================================

set -euo pipefail

REGION="${1:-us-east-1}"

echo "============================================================"
echo "   AWS INFRASTRUCTURE INVENTORY & FINOPS AUDIT (${REGION})"
echo "============================================================"

echo -e "\n[1] RUNNING EC2 INSTANCES"
aws ec2 describe-instances \
    --region "$REGION" \
    --filters "Name=instance-state-name,Values=running" \
    --query "Reservations[].Instances[].{ID:InstanceId,Type:InstanceType,PrivateIP:PrivateIpAddress,Name:Tags[?Key=='Name']|[0].Value}" \
    --output table

echo -e "\n[2] UNATTACHED (AVAILABLE) EBS VOLUMES - FINOPS WASTE CHECK"
aws ec2 describe-volumes \
    --region "$REGION" \
    --filters "Name=status,Values=available" \
    --query "Volumes[].{VolumeId:VolumeId,SizeGB:Size,Type:VolumeType,AZ:AvailabilityZone,Created:CreateTime}" \
    --output table

echo -e "\n[3] UNASSOCIATED ELASTIC IPs (EIPs)"
aws ec2 describe-addresses \
    --region "$REGION" \
    --query "Addresses[?AssociationId==null].{PublicIP:PublicIp,AllocationId:AllocationId}" \
    --output table
