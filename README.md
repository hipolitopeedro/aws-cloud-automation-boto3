# AWS Cloud Administration & Security Automation (Boto3 / AWS CLI)

![AWS](https://img.shields.io/badge/Amazon_AWS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Bash](https://img.shields.io/badge/AWS_CLI_%2F_Bash-121011?style=for-the-badge&logo=gnu-bash&logoColor=white)

> **English:** Automation toolkit built with **Python (`boto3`)** and **AWS CLI** for cloud infrastructure administration, security posture auditing (S3 & IAM), automated EBS backup retention, and FinOps cost optimization (identifying unattached EBS volumes and unused Elastic IPs).
>
> **Português:** Conjunto de automações em **Python (`boto3`)** e **AWS CLI** para administração de infraestrutura em nuvem, auditoria de segurança (S3 e IAM), gerenciamento de retenção de snapshots EBS e otimização de custos FinOps (identificação de volumes EBS órfãos e Elastic IPs ociosos).

---

## Included Tools / Ferramentas Inclusas

| Script | Description (EN) | Descrição (PT-BR) |
| :--- | :--- | :--- |
| [`src/ec2_snapshot_manager.py`](src/ec2_snapshot_manager.py) | Creates EBS snapshots for EC2 instances tagged with `Backup=true` and automatically deletes snapshots older than the retention period (default: 14 days). | Cria snapshots de volumes EBS para instâncias EC2 com a tag `Backup=true` e remove automaticamente snapshots mais antigos que o período de retenção. |
| [`src/s3_security_auditor.py`](src/s3_security_auditor.py) | Audits all S3 buckets in the AWS account for Public Access Block settings, Default Server-Side Encryption (SSE-S3 / KMS), and Versioning. | Audita todos os buckets S3 da conta AWS verificando bloqueio de acesso público, criptografia padrão (SSE-S3 / KMS) e versionamento. |
| [`src/iam_credential_audit.py`](src/iam_credential_audit.py) | Inspects IAM users to detect accounts without MFA enabled and Access Keys older than `N` days (default: 90 days), exporting a JSON compliance report. | Inspeciona usuários IAM para identificar contas sem MFA ativo e Access Keys com mais de `N` dias de uso, gerando relatório de conformidade. |
| [`scripts/aws-cost-and-inventory.sh`](scripts/aws-cost-and-inventory.sh) | AWS CLI script that lists running EC2 instances, unattached (`available`) EBS volumes, and unassociated Elastic IPs to reduce cloud waste. | Script em AWS CLI que lista instâncias EC2 em execução, volumes EBS desanexados (`available`) e Elastic IPs não associados para redução de custos. |

---

## Setup & Usage / Configuração e Uso

### Prerequisites / Pré-requisitos
```bash
pip install -r requirements.txt
aws configure
```

### 1. S3 Security Posture Audit / Auditoria de Segurança no S3
```bash
python src/s3_security_auditor.py --output s3_audit_report.json
```

### 2. IAM MFA & Access Key Rotation Audit / Auditoria de Credenciais IAM
```bash
python src/iam_credential_audit.py --max-key-age-days 90
```

### 3. Automated EBS Snapshot Lifecycle / Gerenciamento de Snapshots EBS
```bash
# Dry-run mode (simulates snapshot creation and cleanup without modifying resources)
python src/ec2_snapshot_manager.py --region us-east-1 --retention-days 14 --dry-run

# Execute backup and rotation
python src/ec2_snapshot_manager.py --region us-east-1 --retention-days 14
```

### 4. FinOps & Unused Resource Inventory / Inventário de Recursos e Custos
```bash
chmod +x scripts/aws-cost-and-inventory.sh
./scripts/aws-cost-and-inventory.sh us-east-1
```
