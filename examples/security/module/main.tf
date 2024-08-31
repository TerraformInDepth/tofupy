
data "aws_vpc" "default" {
  #default = true
  id = "vpc-6a2c9111"
}

resource "aws_security_group" "example" {
  name   = "example_group"
  vpc_id = data.aws_vpc.default.id
}

resource "aws_vpc_security_group_ingress_rule" "example" {
  security_group_id = aws_security_group.example.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  ip_protocol       = "tcp"
  to_port           = 443
}
