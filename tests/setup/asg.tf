resource "aws_launch_template" "test" {
  name                   = "test"
  instance_type          = "t2.micro"
  image_id               = "ami-0c55b159cbfafe1f0"
  key_name               = aws_key_pair.instance.key_name
  vpc_security_group_ids = [aws_security_group.test.id]

  iam_instance_profile {
    name = aws_iam_instance_profile.test.name
  }

  network_interfaces {
    associate_public_ip_address = true
  }

  block_device_mappings {
    device_name = "/dev/sda1"

    ebs {
      delete_on_termination = true
      volume_type           = "gp2"
      volume_size           = 10
    }
  }
}

resource "aws_autoscaling_group" "test" {
  name                = "test-asg"
  vpc_zone_identifier = [aws_subnet.public.id]
  min_size            = 0
  max_size            = 2
  desired_capacity    = 1

  launch_template {
    id      = aws_launch_template.test.id
    version = "$Latest"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_iam_instance_profile" "test" {
  name = "test"
  role = aws_iam_role.test.name
}


resource "aws_iam_role" "test" {
  name = "test"

  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
POLICY

}

resource "aws_security_group" "test" {
  name   = "test"
  vpc_id = aws_vpc.test.id

  ingress {
    from_port   = 80
    to_port     = 80
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

resource "aws_key_pair" "instance" {
  key_name   = "instance"
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDQ6Q6Z"
}
