
output "test_asg_name" {
  description = "The name of the autoscaling group used in the test setup"
  value       = aws_autoscaling_group.test.name
}

output "tests_route53_zone_id" {
  description = "The ID of the Route53 zone used in the test setup"
  value       = aws_route53_zone.test.zone_id
}

output "test_route53_zone_name" {
  description = "The name of the Route53 zone used in the test setup"
  value       = aws_route53_zone.test.name
}

output "test_public_subnet_id" {
  description = "The ID of the public subnet used in the test setup"
  value       = aws_subnet.public.id
}
