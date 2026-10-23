terraform {
  backend "s3" {
    bucket         = "eks-pern-terraform-state"
    key            = "eks/terraform.tfstate"
    region         = var.region
    dynamodb_table = "terraform-lock"
    encrypt        = true
  }
}