# from typing import List

# from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel, LifecycleTransition
# from app.components.metadata.internal.instance_metadata_base_service import InstanceMetadataBaseService
# from app.components.metadata.models.metadata_result_model import MetadataResultModel
# from app.config.models.dns_record_config import DnsRecordConfig
# from app.config.models.scaling_group_config import ScalingGroupConfiguration


# class MockDnsValueResolverService(InstanceMetadataBaseService):
#     def handle_ip_source(
#         self,
#         sg_config_item: ScalingGroupConfiguration,
#         lifecycle_event: LifecycleEventModel,
#         ip_type: str,
#     ) -> List[MetadataResultModel]:
#         return [
#             MetadataResultModel("id-1", "192.168.0.1"),
#             MetadataResultModel("id-2", "192.168.0.2"),
#         ]

#     def handle_tag_source(
#         self,
#         sg_config_item: ScalingGroupConfiguration,
#         lifecycle_event: LifecycleEventModel,
#         tag_name: str,
#     ) -> List[MetadataResultModel]:
#         return [
#             MetadataResultModel("id-1", "example.com"),
#         ]


# def test_resolve_dns_value_with_ip_source():
#     resolver = MockDnsValueResolverService()
#     sg_config_item = ScalingGroupConfiguration(
#         scaling_group_name="test-sg",
#         dns_config=DnsRecordConfig(value_source="ip:public", record_type="A", record_ttl=60),
#     )
#     lifecycle_event = LifecycleEventModel(
#         transition=LifecycleTransition.LAUNCHING,
#         lifecycle_hook_name="test-hook",
#         scaling_group_name="test-sg",
#         instance_id="i-12345",
#     )
#     result = resolver.resolve_value(sg_config_item, lifecycle_event)
#     assert [item.value for item in result] == ["192.168.0.1", "192.168.0.2"]


# def test_resolve_dns_value_with_tag_source():
#     resolver = MockDnsValueResolverService()
#     sg_config_item = ScalingGroupConfiguration(
#         scaling_group_name="test-sg",
#         dns_config=DnsRecordConfig(value_source="tag:example_tag", record_type="A", record_ttl=60),
#     )
#     lifecycle_event = LifecycleEventModel(
#         transition=LifecycleTransition.LAUNCHING,
#         lifecycle_hook_name="test-hook",
#         scaling_group_name="test-sg",
#         instance_id="i-12345",
#     )
#     result = resolver.resolve_value(sg_config_item, lifecycle_event)
#     assert [item.value for item in result] == ["example.com"]


# def test_resolve_dns_value_with_unknown_source():
#     resolver = MockDnsValueResolverService()
#     sg_config_item = ScalingGroupConfiguration(
#         scaling_group_name="test-sg",
#         dns_config=DnsRecordConfig(value_source="unknown_source", record_type="A", record_ttl=60),
#     )
#     lifecycle_event = LifecycleEventModel(
#         transition=LifecycleTransition.LAUNCHING,
#         lifecycle_hook_name="test-hook",
#         scaling_group_name="test-sg",
#         instance_id="i-12345",
#     )
#     result = resolver.resolve_value(sg_config_item, lifecycle_event)
#     assert result is None
