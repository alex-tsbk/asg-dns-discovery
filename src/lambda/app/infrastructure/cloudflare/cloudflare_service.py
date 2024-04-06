class CloudflareService:
    def read_record(self, hosted_zone_id: str, record_name: str, record_type: str) -> None:
        raise NotImplementedError()
