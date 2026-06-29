provider "aws" {
  region = "ap-south-1"
}

resource "aws_key_pair" "my_key" {
  key_name   = "flask-key"
  public_key = file("mykey.pub")
}

resource "aws_security_group" "flask_sg" {
  name        = "flask-sg"
  description = "Allow SSH, HTTP, Flask"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "flask_ec2" {
  ami           = "ami-0f5ee92e2d63afc18"
  instance_type = "t3.micro"

  key_name      = aws_key_pair.my_key.key_name
  vpc_security_group_ids = [aws_security_group.flask_sg.id]

  user_data = file("user_data.sh")

  tags = {
    Name = "LearnOrbit School-ERP-Flask"
  }
}