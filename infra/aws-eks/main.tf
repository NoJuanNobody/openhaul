terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.24"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "OpenHaul"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# --- VPC & Networking ---
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "openhaul-vpc-${var.environment}"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = var.environment == "staging" ? true : false
  enable_dns_hostnames = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
    "karpenter.sh/discovery"          = "openhaul-eks-${var.environment}"
  }
}

# --- AWS EKS Cluster ---
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "openhaul-eks-${var.environment}"
  cluster_version = "1.30"

  cluster_endpoint_public_access = true

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    core_system = {
      min_size     = 2
      max_size     = 5
      desired_size = 2
      instance_types = ["c6i.xlarge"]
      capacity_type  = "ON_DEMAND"
      labels = {
        "openhaul.network/role" = "system-core"
      }
    }
    nitro_enclaves = {
      min_size     = 1
      max_size     = 4
      desired_size = 1
      instance_types = ["c6i.2xlarge"]
      capacity_type  = "ON_DEMAND"
      # Enable AWS Nitro Enclaves for ZK-Escrow key management
      enclave_options = {
        enabled = true
      }
      labels = {
        "openhaul.network/role" = "zk-nitro-enclave"
      }
    }
  }

  tags = {
    "karpenter.sh/discovery" = "openhaul-eks-${var.environment}"
  }
}

# --- AWS IoT Core for Telematics Fleet Gateway ---
resource "aws_iot_thing_type" "fleet_eld" {
  name = "OpenHaul_ELD_Gateway"
  properties {
    description = "Electronic Logging Device & Telematics Ingestion Unit"
  }
}

resource "aws_iot_topic_rule" "telematics_stream" {
  name        = "openhaul_telematics_ingest_${var.environment}"
  description = "Ingest real-time GPS and engine telematics into Kinesis/Kafka"
  enabled     = true
  sql         = "SELECT *, clientid() as vehicle_id, timestamp() as ts FROM 'openhaul/fleet/+/telematics'"
  sql_version = "2016-03-23"

  republish {
    role_arn = aws_iam_role.iot_republish_role.arn
    topic    = "openhaul/internal/dispatch/stream"
    qos      = 1
  }
}

resource "aws_iam_role" "iot_republish_role" {
  name = "openhaul-iot-republish-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "iot.amazonaws.com"
      }
    }]
  })
}
