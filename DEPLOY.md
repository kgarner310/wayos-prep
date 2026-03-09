# Deploying WAYOS PREP to AWS ECS/Fargate

Step-by-step guide from zero to production. Assumes no prior AWS experience.

---

## 1. Prerequisites

### Create an AWS Account

1. Go to https://aws.amazon.com and click **Create an AWS Account**
2. Enter email, password, and account name
3. Add a payment method (you won't be charged until you use paid services)
4. Choose the **Basic (Free)** support plan

### Create an IAM User (don't use root for daily work)

1. Sign in to the AWS Console at https://console.aws.amazon.com
2. Search for **IAM** in the top search bar, open it
3. Click **Users** > **Create user**
4. Name: `wayos-deploy`
5. Check **Provide user access to the AWS Management Console** (optional — for console access)
6. Click **Next**, then **Attach policies directly**
7. Search and check: **AdministratorAccess** (we'll scope this down later)
8. Click **Create user**
9. On the user page, go to **Security credentials** tab > **Create access key**
10. Choose **Command Line Interface (CLI)**
11. **Save the Access Key ID and Secret Access Key** — you won't see the secret again

### Install AWS CLI

```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Windows
# Download from https://awscli.amazonaws.com/AWSCLIV2.msi
```

Configure it:

```bash
aws configure
```

Enter:
- **Access Key ID**: from step 11 above
- **Secret Access Key**: from step 11 above
- **Default region**: `us-east-1`
- **Default output format**: `json`

Verify it works:

```bash
aws sts get-caller-identity
```

You should see your account ID and user ARN.

### Install Terraform

```bash
# macOS
brew install terraform

# Linux
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common
wget -O- https://apt.releases.hashicorp.com/gpg | \
  gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
  https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
  sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt-get update && sudo apt-get install terraform

# Windows
choco install terraform
```

Verify: `terraform --version` (need 1.5+)

---

## 2. Create Secrets in AWS Secrets Manager

Terraform needs the ARNs of your secrets before it can create the ECS task. Create them first.

Replace the placeholder values with your real credentials:

```bash
# Database URL (your Supabase connection string)
aws secretsmanager create-secret \
  --name wayos-prep/database-url \
  --secret-string "postgresql://postgres.[YOUR-REF]:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres" \
  --region us-east-1
```

```bash
# Redis URL (if you have one — otherwise use a placeholder and update later)
aws secretsmanager create-secret \
  --name wayos-prep/redis-url \
  --secret-string "redis://localhost:6379/0" \
  --region us-east-1
```

```bash
# JWT secret (auto-generated)
aws secretsmanager create-secret \
  --name wayos-prep/jwt-secret \
  --secret-string "$(openssl rand -hex 32)" \
  --region us-east-1
```

```bash
# OpenAI API key (if you have one — otherwise use a placeholder)
aws secretsmanager create-secret \
  --name wayos-prep/openai-api-key \
  --secret-string "sk-your-key-here" \
  --region us-east-1
```

Each command prints JSON with an `ARN` field. **Copy all 4 ARNs** — you need them next.

They look like: `arn:aws:secretsmanager:us-east-1:123456789012:secret:wayos-prep/database-url-AbCdEf`

> **To update a secret later:**
> ```bash
> aws secretsmanager update-secret \
>   --secret-id wayos-prep/database-url \
>   --secret-string "new-value-here"
> ```

---

## 3. Configure Terraform

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and paste your 4 ARNs:

```hcl
aws_region  = "us-east-1"
environment = "production"

# ECS sizing — start small, scale up if needed
# 512 CPU = 0.25 vCPU, 1024 memory = 1 GB RAM
ecs_cpu           = 512
ecs_memory        = 1024
ecs_desired_count = 1

# Leave empty for now — we'll add HTTPS in step 7
certificate_arn = ""

# Paste your 4 ARNs here:
database_url_secret_arn   = "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT:secret:wayos-prep/database-url-XXXXXX"
redis_url_secret_arn      = "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT:secret:wayos-prep/redis-url-XXXXXX"
jwt_secret_arn            = "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT:secret:wayos-prep/jwt-secret-XXXXXX"
openai_api_key_secret_arn = "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT:secret:wayos-prep/openai-api-key-XXXXXX"
```

---

## 4. Deploy Infrastructure

```bash
cd infra

# Download provider plugins
terraform init

# Preview what will be created (nothing is changed yet)
terraform plan
```

Review the plan. You should see ~20 resources being created: VPC, subnets, NAT gateway, ALB, ECS cluster, ECR repo, IAM roles, security groups, etc.

```bash
# Create everything (type "yes" when prompted)
terraform apply
```

This takes 2–4 minutes. When done, you'll see outputs:

```
alb_dns_name      = "wayos-prep-alb-123456789.us-east-1.elb.amazonaws.com"
ecr_repository_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/wayos-prep-production"
ecs_cluster_name   = "wayos-prep-production"
ecs_service_name   = "wayos-prep-production"
```

**Save these values** — you'll need the ALB DNS name and ECR URL next.

> **If something goes wrong:** `terraform destroy` tears everything down cleanly.

---

## 5. Push Your First Docker Image

The ECS service is running but has no image yet. Push one manually this first time.

```bash
# Go back to the repo root
cd ..

# Log in to your ECR registry (replace with your ECR URL)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

```bash
# Build the image
docker build -t 123456789012.dkr.ecr.us-east-1.amazonaws.com/wayos-prep-production:latest .
```

```bash
# Push it
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/wayos-prep-production:latest
```

```bash
# Tell ECS to pick up the new image
aws ecs update-service \
  --cluster wayos-prep-production \
  --service wayos-prep-production \
  --force-new-deployment \
  --region us-east-1
```

Wait 1–2 minutes, then verify:

```bash
curl http://wayos-prep-alb-123456789.us-east-1.elb.amazonaws.com/health
```

You should see:

```json
{"service":"wayos-prep","database":"ok","redis":"unavailable","status":"ok"}
```

> **If the health check fails**, check the logs:
> ```bash
> aws logs tail /ecs/wayos-prep-production --follow --region us-east-1
> ```

---

## 6. Set Up GitHub Actions CI/CD

After this, every push to `main` will auto-deploy. No more manual docker builds.

### 6a. Create a GitHub OIDC Identity Provider in AWS

This lets GitHub Actions authenticate with AWS without storing long-lived credentials.

```bash
# Get GitHub's OIDC thumbprint (this rarely changes)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 6b. Create an IAM Role for GitHub Actions

Create a file called `github-trust-policy.json` (don't commit this):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_ORG/wayos-prep:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

Replace `YOUR_ACCOUNT_ID` and `YOUR_GITHUB_ORG` with your values.

```bash
# Create the role
aws iam create-role \
  --role-name wayos-prep-github-deploy \
  --assume-role-policy-document file://github-trust-policy.json
```

### 6c. Attach Permissions to the Role

Create `github-deploy-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "arn:aws:ecr:us-east-1:YOUR_ACCOUNT_ID:repository/wayos-prep-production"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:RegisterTaskDefinition",
        "ecs:UpdateService"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": [
        "arn:aws:iam::YOUR_ACCOUNT_ID:role/wayos-prep-production-execution",
        "arn:aws:iam::YOUR_ACCOUNT_ID:role/wayos-prep-production-task"
      ]
    }
  ]
}
```

```bash
aws iam put-role-policy \
  --role-name wayos-prep-github-deploy \
  --policy-name deploy-permissions \
  --policy-document file://github-deploy-policy.json
```

### 6d. Add the Role ARN to GitHub

1. Get the role ARN:
   ```bash
   aws iam get-role --role-name wayos-prep-github-deploy --query Role.Arn --output text
   ```
2. Go to your GitHub repo > **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Name: `AWS_DEPLOY_ROLE_ARN`
5. Value: the ARN from step 1 (e.g., `arn:aws:iam::123456789012:role/wayos-prep-github-deploy`)

Now push to `main` and watch the **Actions** tab — it should build, push to ECR, and deploy to ECS automatically.

---

## 7. HTTPS (Optional but Recommended)

### 7a. Get an SSL Certificate

1. Go to **AWS Certificate Manager** (ACM) in the console: https://console.aws.amazon.com/acm
2. Click **Request a certificate** > **Request a public certificate**
3. Enter your domain name (e.g., `api.wayos.ai`)
4. Choose **DNS validation**
5. Click **Request**

### 7b. Validate the Certificate

ACM shows a CNAME record you need to add to your DNS. If your domain is in Route 53:
- Click **Create records in Route 53** — done automatically

If your domain is elsewhere (GoDaddy, Namecheap, etc.):
- Add the CNAME record shown in ACM to your DNS provider
- Wait a few minutes for validation (status changes to "Issued")

### 7c. Apply the Certificate

Once the certificate status is **Issued**, copy its ARN from the ACM console.

Edit `infra/terraform.tfvars`:

```hcl
certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/abc-123-def-456"
```

```bash
cd infra
terraform apply
```

### 7d. Point Your Domain to the ALB

Add a DNS record pointing your domain to the ALB:

- **Type**: CNAME (or ALIAS if using Route 53)
- **Name**: `api.wayos.ai` (your domain)
- **Value**: `wayos-prep-alb-123456789.us-east-1.elb.amazonaws.com` (your ALB DNS from step 4)

After DNS propagates (minutes to hours):

```bash
curl https://api.wayos.ai/health
```

### 7e. Update CORS

Update the `CORS_ORIGINS` secret or environment variable to include your domain:

In `infra/modules/ecs/main.tf`, add to the `environment` list:

```hcl
{ name = "CORS_ORIGINS", value = "https://app.wayos.ai" },
```

Then `terraform apply`.

---

## 8. Monitoring and Logs

### View Live Logs

```bash
aws logs tail /ecs/wayos-prep-production --follow --region us-east-1
```

### Check Service Health

```bash
# ALB health
curl http://YOUR_ALB_DNS/health

# ECS service status
aws ecs describe-services \
  --cluster wayos-prep-production \
  --services wayos-prep-production \
  --query 'services[0].{status:status,running:runningCount,desired:desiredCount,deployments:deployments[*].{status:status,running:runningCount}}' \
  --region us-east-1
```

### View in AWS Console

- **ECS**: https://console.aws.amazon.com/ecs — see tasks, CPU/memory, restarts
- **CloudWatch Logs**: https://console.aws.amazon.com/cloudwatch — search and filter logs
- **ALB**: https://console.aws.amazon.com/ec2/v2/home#LoadBalancers — request counts, latency, errors

---

## 9. Cost Estimate

Monthly cost at minimum config (1 task, 0.25 vCPU, 1 GB RAM):

| Service | Cost/Month |
|---|---|
| ECS Fargate (1 task, always on) | ~$15 |
| Application Load Balancer | ~$16 |
| NAT Gateway | ~$32 + $0.045/GB data |
| ECR (image storage) | ~$1 |
| Secrets Manager (4 secrets) | ~$2 |
| CloudWatch Logs | ~$1 |
| **Total** | **~$67/mo** |

### Tips to Reduce Cost

- **NAT Gateway is the biggest fixed cost.** For a dev/staging environment, you can skip it by putting ECS tasks in public subnets with `assign_public_ip = true` in the ECS module. This saves ~$32/mo but is less secure (tasks get public IPs).
- **Scale to zero** when not in use: `aws ecs update-service --cluster wayos-prep-production --service wayos-prep-production --desired-count 0`
- **Scale back up**: same command with `--desired-count 1`

---

## 10. Common Operations

### Redeploy Manually

```bash
aws ecs update-service \
  --cluster wayos-prep-production \
  --service wayos-prep-production \
  --force-new-deployment
```

### Update a Secret

```bash
aws secretsmanager update-secret \
  --secret-id wayos-prep/database-url \
  --secret-string "postgresql://new-connection-string"

# ECS caches secrets — force a redeploy to pick up the change:
aws ecs update-service \
  --cluster wayos-prep-production \
  --service wayos-prep-production \
  --force-new-deployment
```

### Tear Everything Down

```bash
cd infra
terraform destroy
```

This removes all AWS resources. Your secrets in Secrets Manager are **not** deleted by Terraform (they have a 30-day recovery window). To delete them immediately:

```bash
aws secretsmanager delete-secret --secret-id wayos-prep/database-url --force-delete-without-recovery
aws secretsmanager delete-secret --secret-id wayos-prep/redis-url --force-delete-without-recovery
aws secretsmanager delete-secret --secret-id wayos-prep/jwt-secret --force-delete-without-recovery
aws secretsmanager delete-secret --secret-id wayos-prep/openai-api-key --force-delete-without-recovery
```

---

## Troubleshooting

### ECS task keeps restarting

Check logs first:
```bash
aws logs tail /ecs/wayos-prep-production --follow
```

Common causes:
- **Database unreachable**: verify your Supabase DATABASE_URL secret is correct
- **Out of memory**: increase `ecs_memory` in terraform.tfvars and re-apply
- **Health check failing**: the ALB expects `GET /health` to return 200 within 10 seconds

### "Unable to assume role" in GitHub Actions

- Verify the OIDC provider exists: `aws iam list-open-id-connect-providers`
- Check the trust policy matches your exact GitHub org/repo name
- Make sure you're pushing to the `main` branch (the trust policy restricts to `refs/heads/main`)

### Terraform state issues

If someone else also manages this infra, set up remote state to avoid conflicts. Uncomment the `backend "s3"` block in `infra/main.tf` and create the S3 bucket + DynamoDB table:

```bash
aws s3api create-bucket --bucket wayos-prep-tfstate --region us-east-1
aws dynamodb create-table \
  --table-name wayos-prep-tflock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

Then `terraform init -migrate-state` to move your local state to S3.
