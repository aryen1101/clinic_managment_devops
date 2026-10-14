# AWS infrastructure for CareDesk Clinic Management:
#
#   VPC (10.30.0.0/16)
#    ├── 2 public subnets   (load balancers, NAT gateway)
#    ├── 2 private subnets  (EKS worker nodes)
#    ├── Internet gateway + 1 NAT gateway
#    └── EKS cluster
#          ├── managed node group (t3.medium x2)
#          └── add-ons: coredns, kube-proxy, vpc-cni, pod identity, EBS CSI (for the Postgres PVC)

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  azs = slice(data.aws_availability_zones.available.names, 0, var.az_count)

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ---------------------------------------------------------------- Network
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.21"

  name = "${var.project_name}-vpc"
  cidr = var.vpc_cidr
  azs  = local.azs

  # 10.30.1.0/24, 10.30.2.0/24 ... private | 10.30.101.0/24, 10.30.102.0/24 ... public
  private_subnets = [for i, _ in local.azs : cidrsubnet(var.vpc_cidr, 8, i + 1)]
  public_subnets  = [for i, _ in local.azs : cidrsubnet(var.vpc_cidr, 8, i + 101)]

  enable_nat_gateway   = true
  single_nat_gateway   = true # one NAT keeps the classroom bill low; use one per AZ in production
  enable_dns_hostnames = true
  enable_dns_support   = true

  # Tags that let Kubernetes place public / internal load balancers in the right subnets
  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }
}

# ---------------------------------------------------------------- EKS
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.37"

  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access           = true # lets kubectl on your laptop reach the API server
  enable_cluster_creator_admin_permissions = true # the IAM identity running terraform becomes cluster admin

  cluster_addons = {
    coredns                = {}
    kube-proxy             = {}
    vpc-cni                = { before_compute = true }
    eks-pod-identity-agent = { before_compute = true }
    aws-ebs-csi-driver     = {} # needed for PersistentVolumeClaims (Postgres)
  }

  eks_managed_node_groups = {
    default = {
      ami_type       = "AL2023_x86_64_STANDARD"
      instance_types = var.node_instance_types
      capacity_type  = "ON_DEMAND"

      min_size     = var.node_min_size
      desired_size = var.node_desired_size
      max_size     = var.node_max_size

      # Lets the EBS CSI driver (running on the nodes) create and attach EBS volumes
      iam_role_additional_policies = {
        ebs_csi = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
      }

      labels = {
        workload = "clinic"
      }
    }
  }
}
