import re

import pytest
from app.components.dns.internal.aws.aws_dns_change_request_model import (
    AwsDnsChangeRequestModel,
    DnsChangeRequestAction,
    DnsRecordType,
)
from app.utils.exceptions import BusinessException

MOCK_HOSTED_ZONE_ID = "Z1234567890"
MOCK_DNS_DOMAIN = "test.example.com"


@pytest.fixture
def dns_record_A():
    dns_record = AwsDnsChangeRequestModel(
        action=DnsChangeRequestAction.CREATE,
        hosted_zone_id=MOCK_HOSTED_ZONE_ID,
        record_name=MOCK_DNS_DOMAIN,
        record_type=DnsRecordType("A"),
        record_ttl=3600,
    )
    yield dns_record


def test_get_change(dns_record_A: AwsDnsChangeRequestModel):
    model = dns_record_A
    model._change = {
        "Action": "UPSERT",
        "ResourceRecordSet": {
            "Name": MOCK_DNS_DOMAIN,
            "Type": "A",
            "TTL": 3600,
            "ResourceRecords": [{"Value": "192.168.0.1"}, {"Value": "192.168.0.2"}],
        },
    }
    expected_change = {
        "Changes": [
            {
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": MOCK_DNS_DOMAIN,
                    "Type": "A",
                    "TTL": 3600,
                    "ResourceRecords": [{"Value": "192.168.0.1"}, {"Value": "192.168.0.2"}],
                },
            }
        ]
    }
    assert model.get_change()["Changes"] == expected_change["Changes"]


def test_build_change_with_A_record(dns_record_A: AwsDnsChangeRequestModel):
    model = dns_record_A
    model.record_values = ["192.168.0.1", "192.168.0.2"]
    expected_change = {
        "Action": "UPSERT",
        "ResourceRecordSet": {
            "Name": MOCK_DNS_DOMAIN,
            "Type": "A",
            "TTL": 3600,
            "ResourceRecords": [{"Value": "192.168.0.1"}, {"Value": "192.168.0.2"}],
        },
    }
    assert model.build_change()._change == expected_change


def test_build_change_with_unsupported_record_type(dns_record_A: AwsDnsChangeRequestModel):
    model = dns_record_A
    model.record_type = "UNSUPPORTED"  # type: ignore
    with pytest.raises(BusinessException):
        model.build_change()


def test_get_route53_change_action_name():
    assert AwsDnsChangeRequestModel._get_route53_change_action_name(DnsChangeRequestAction.CREATE) == "UPSERT"
    assert AwsDnsChangeRequestModel._get_route53_change_action_name(DnsChangeRequestAction.UPDATE) == "UPSERT"
    assert AwsDnsChangeRequestModel._get_route53_change_action_name(DnsChangeRequestAction.DELETE) == "DELETE"

    with pytest.raises(ValueError):
        AwsDnsChangeRequestModel._get_route53_change_action_name("INVALID_ACTION")
