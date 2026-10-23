# Get available AZs dynamically
data "aws_availability_zones" "available" {}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

data "aws_ami" "ubuntu" {
  most_recent = true

  owners = ["099720109477"] 

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}