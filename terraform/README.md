# Terraform — AWS VPC + EKS

Infrastructure as Code for running CareDesk on AWS. Kubernetes only manages workloads; Terraform creates the network and the cluster those workloads run on.

```text
AWS (ap-south-1)
└── VPC 10.30.0.0/16
    ├── public subnets   10.30.101.0/24, 10.30.102.0/24   (load balancers, NAT gateway)
    ├── private subnets  10.30.1.0/24,   10.30.2.0/24     (worker nodes)
    ├── internet gateway + 1 NAT gateway
    └── EKS cluster "clinic-eks" (Kubernetes 1.33)
        ├── managed node group: 2 x t3.medium (min 1, max 3), Amazon Linux 2023
        └── add-ons: coredns, kube-proxy, vpc-cni, pod-identity-agent, aws-ebs-csi-driver
```

| File | Purpose |
|---|---|
| `versions.tf` | Terraform + AWS provider versions, provider config, optional S3 remote state |
| `variables.tf` | Inputs (region, names, CIDR, node sizes) with defaults |
| `main.tf` | VPC module + EKS module |
| `outputs.tf` | VPC/subnet IDs, cluster endpoint, ready-made `aws eks update-kubeconfig` command |
| `terraform.tfvars.example` | Example inputs. Copy it to `terraform.tfvars` (git-ignored) |
| `.terraform.lock.hcl` | Pins exact provider versions. **Commit it.** |

## Commands

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars     # optional
terraform init          # download providers + modules
terraform fmt -check    # formatting
terraform validate      # syntax/semantics (no AWS credentials needed)
terraform plan          # needs AWS credentials: shows what WOULD be created (~60 resources)
terraform apply         # ~15-20 min: creates everything
$(terraform output -raw configure_kubectl)       # point kubectl at EKS
terraform destroy       # delete everything; do this the same day!
```

> **No AWS credentials?** The instructor said running `apply` isn't required. Submit screenshots of `init` + `validate` (and `plan` if you have any AWS access). The `.tf` files are what gets graded.

> **Cost warning:** EKS control plane (~$0.10/h) + NAT gateway (~$0.05/h + data) + 2× t3.medium (~$0.09/h) comes to roughly **$6–7 per day**. Set an AWS Budget alert and run `terraform destroy` as soon as you have your screenshots.

## Deploying the app onto EKS (optional)

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace
kubectl create namespace clinic
kubectl -n clinic create secret generic clinic-db-secret --from-literal=DB_USER=clinic --from-literal=DB_PASSWORD='<strong-password>'
helm upgrade --install clinic ./helm/clinic -n clinic -f helm/clinic/values-prod.yaml \
  --set backend.tag=<sha> --set frontend.tag=<sha> \
  --set backend.image=ghcr.io/<you>/clinic-backend --set frontend.image=ghcr.io/<you>/clinic-frontend
kubectl get svc -n ingress-nginx   # EXTERNAL-IP = AWS load balancer hostname
```
Run `helm uninstall` and delete the ingress-nginx release **before** `terraform destroy`, so the AWS load balancer it created gets removed too.
