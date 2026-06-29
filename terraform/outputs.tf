output "public_ip" {
  value = aws_instance.flask_ec2.public_ip
}

output "Machine_name" {
  value = aws_instance.flask_ec2.ami
}