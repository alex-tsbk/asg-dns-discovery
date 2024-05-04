from dataclasses import dataclass

import boto3
from mypy_boto3_ec2 import EC2Client, EC2ServiceResource
from mypy_boto3_ec2.service_resource import SecurityGroup, Subnet, Vpc
from mypy_boto3_ec2.type_defs import KeyPairTypeDef


@dataclass
class NetworkingSeederResponse:
    vpc: Vpc
    subnet: Subnet
    security_group: SecurityGroup
    ec2_key_pair: KeyPairTypeDef

    @property
    def vpc_id(self) -> str:
        return self.vpc.id

    @property
    def subnet_id(self) -> str:
        return self.subnet.id

    @property
    def security_group_id(self) -> str:
        return self.security_group.id

    @property
    def ec2_key_name(self) -> str:
        return self.ec2_key_pair["KeyName"]


class NetworkingSeeder:
    def __init__(self):
        self.ec2_resource: EC2ServiceResource = boto3.resource("ec2")  # type: ignore
        self.ec2_client: EC2Client = boto3.client("ec2")  # type: ignore

    def setup_aws_networking(self):
        # Create VPC
        vpc = self.ec2_resource.create_vpc(CidrBlock="10.0.0.0/16")
        vpc.wait_until_available()
        vpc.modify_attribute(EnableDnsSupport={"Value": True})
        vpc.modify_attribute(EnableDnsHostnames={"Value": True})

        # Create subnet
        subnet = self.ec2_resource.create_subnet(CidrBlock="10.0.1.0/24", VpcId=vpc.id)

        # Create Internet Gateway and attach to VPC
        ig = self.ec2_resource.create_internet_gateway()
        vpc.attach_internet_gateway(InternetGatewayId=ig.id)

        # Create a route table and a public route
        route_table = vpc.create_route_table()
        route_table.create_route(DestinationCidrBlock="0.0.0.0/0", GatewayId=ig.id)

        # Associate the route table with the subnet
        route_table.associate_with_subnet(SubnetId=subnet.id)

        # Create a security group
        sec_group = self.ec2_resource.create_security_group(
            GroupName="slice_0_sg", Description="Security group for integration testing", VpcId=vpc.id
        )
        sec_group.authorize_ingress(CidrIp="0.0.0.0/0", IpProtocol="tcp", FromPort=22, ToPort=22)

        # Create an EC2 key pair
        key_name = "ec2-keypair"
        ec2_key_pair = self.ec2_client.create_key_pair(KeyName=key_name)

        # Create and return the response dataclass
        return NetworkingSeederResponse(
            vpc=vpc,
            subnet=subnet,
            security_group=sec_group,
            ec2_key_pair=ec2_key_pair,
        )
