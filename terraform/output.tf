output "ec2_global_ips" {
  value = ["${aws_instance.test-instance.*.public_ip}"]
}

  