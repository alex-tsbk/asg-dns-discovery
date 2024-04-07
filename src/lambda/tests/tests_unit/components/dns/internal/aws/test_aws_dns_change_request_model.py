import pytest
from app.components.dns.internal.aws.aws_dns_change_request_model import (
    AwsDnsChangeRequestModel,
    DnsChangeRequestAction,
    DnsRecordType,
)


def test_get_change():
    model = AwsDnsChangeRequestModel(
        action=DnsChangeRequestAction.CREATE,
        record_name="example.com",
        record_type=DnsRecordType("A"),
    )
    model.record_type = "A"
    model._change = {
        "Action": "UPSERT",
        "ResourceRecordSet": {
            "Name": "example.com",
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
                    "Name": "example.com",
                    "Type": "A",
                    "TTL": 3600,
                    "ResourceRecords": [{"Value": "192.168.0.1"}, {"Value": "192.168.0.2"}],
                },
            }
        ]
    }
    assert model.get_change() == expected_change


def test_build_change_with_A_record():
    model = AwsDnsChangeRequestModel(
        action=DnsChangeRequestAction.CREATE,
        record_name="example.com",
        record_type=DnsRecordType("A"),
        record_ttl=3600,
        record_values=["192.168.0.1", "192.168.0.2"],
    )
    expected_change = {
        "Action": "UPSERT",
        "ResourceRecordSet": {
            "Name": "example.com",
            "Type": "A",
            "TTL": 3600,
            "ResourceRecords": [{"Value": "192.168.0.1"}, {"Value": "192.168.0.2"}],
        },
    }
    assert model.build_change()._change == expected_change


def test_build_change_with_unsupported_record_type():
    model = AwsDnsChangeRequestModel(
        action=DnsChangeRequestAction.CREATE,
        record_name="example.com",
        record_type="UNSUPPORTED",
        record_ttl=3600,
        record_values=["example.com"],
    )
    with pytest.raises(NotImplementedError):
        model.build_change()


def test_get_route53_change_action_name():
    assert AwsDnsChangeRequestModel._get_route53_change_action_name(DnsChangeRequestAction.CREATE) == "UPSERT"
    assert AwsDnsChangeRequestModel._get_route53_change_action_name(DnsChangeRequestAction.UPDATE) == "UPSERT"
    assert AwsDnsChangeRequestModel._get_route53_change_action_name(DnsChangeRequestAction.DELETE) == "DELETE"

    with pytest.raises(ValueError):
        AwsDnsChangeRequestModel._get_route53_change_action_name("INVALID_ACTION")
