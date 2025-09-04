terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}




provider "aws" {
  # Specifies the desired AWS region for resource provisioning
  region = "us-east-1"
}


resource "aws_instance" "test-instance" {
  ami             = var.ami
  instance_type   = var.instance_type
  key_name        = var.key_pair
  security_groups = [aws_security_group.Oroshine-security-group.name]

  user_data = file("${path.module}/automation.sh")

  tags = {
    Name = "oroshine_app"
  }
}


resource "aws_security_group" "Oroshine-security-group" {
  name = "Oroshine-security-group"

  #Incoming traffic
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] #replace it with your ip address
  }

  #Outgoing traffic
  egress {
    from_port   = 0
    protocol    = "-1"
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  #Incoming traffic
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] #replace it with your ip address
  }

  #Outgoing traffic
  egress {
    from_port   = 0
    protocol    = "-1"
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  #Incoming traffic
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] #replace it with your ip address
  }

  #Outgoing traffic
  egress {
    from_port   = 0
    protocol    = "-1"
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "Oroshine-security-group"
  }

}

