from typing import Optional
from schema_registry.client.utils import SchemaVersion

class KafkaTopicMetadata:

    def __init__(self, name: str) -> None:
        super().__init__()

        assert (name and name.strip()), "Kafka topic metadata name is invalid"
        self._name = name
        self.safe_timestamp = 0
        self.schema = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def sanitized_name(self) -> str:
        return self.name.replace(".","_")

    @property
    def safe_timestamp(self) -> int:
        return self._safe_timestamp

    @safe_timestamp.setter
    def safe_timestamp(self, value: int):
        self._safe_timestamp = value

    @property
    def schema(self) -> Optional[SchemaVersion]:
        return self._schema

    @schema.setter
    def schema(self, value: SchemaVersion):
        self._schema = value
