from typing import List, Dict, Optional
from kafka.consumer import KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic, ConfigResource, ConfigResourceType
from kafka.structs import TopicPartition
from schema_registry.client import SchemaRegistryClient, schema
from schema_registry.client.utils import SchemaVersion
from schema_registry.client.schema import AvroSchema

class KafkaManager:

    def __init__(self, bootstrap_servers: List[str], schema_registry_url: str = None):
        super().__init__()
        self._admin = KafkaAdminClient(
            bootstrap_servers=','.join(bootstrap_servers)
        )
        self._consumer = KafkaConsumer(
            bootstrap_servers=','.join(bootstrap_servers),
            client_id="py_kafka_manager",
            auto_offset_reset='earliest'
        )
        self._schema_registry = None if schema_registry_url is None else SchemaRegistryClient(schema_registry_url)

    def get_topics(self)->List[str]:
        topics = []
        for topic in self._consumer.topics():
            topics.append(topic)

        return topics
    
    def create_topic(self, topic_name: str, partitions: int, replicas: int):
        topic = NewTopic(name=topic_name, num_partitions=partitions, replication_factor=replicas)
        self._admin.create_topics([topic])
    
    def get_topic_partitions(self, topic: str)->List[TopicPartition]:
        topic_partitions: List[TopicPartition] = []
        partitions = self._consumer.partitions_for_topic(topic)
        if partitions is None:
            return topic_partitions

        for partition in partitions:
            topic_partitions.append(TopicPartition(topic, partition))

        return topic_partitions

    def get_last_partition_message(self, partition: TopicPartition):
        end_offsets = self._consumer.end_offsets([partition])
        start_offsets = self._consumer.beginning_offsets([partition])
        self._consumer.assign([partition])

        if (end_offsets[partition] == start_offsets[partition]):
            return None

        last_message_offset=end_offsets[partition]-1 if end_offsets[partition]>0 else end_offsets[partition]
        self._consumer.seek(partition,last_message_offset)
        message = self._consumer.poll(timeout_ms=10000, max_records=1)
        if len(message) == 0:
            raise Exception(F"No Message loaded from Topic [{partition.topic}] Partition [{partition.partition}]")
        last_partition_messages = message[partition]

        if len(last_partition_messages) == 0:
            return None
        return last_partition_messages[len(last_partition_messages)-1]

    def get_topic_last_safe_timestamp(self, topic: str)->int:
        message_timestamp = 0

        for partition in self.get_topic_partitions(topic):
            message = self.get_last_partition_message(partition)
            if message is None:
                continue
            if message_timestamp == 0 or message_timestamp<message.timestamp:
                    message_timestamp = message.timestamp

        return message_timestamp

    def get_schema_by_id(self, schema_id: int) -> Optional[AvroSchema]:
        if self._schema_registry is None:
            return None
        
        return self._schema_registry.get_by_id(schema_id=schema_id)
        
    def get_last_topic_value_schema(self, topic: str)-> Optional[SchemaVersion]:
        if self._schema_registry is None:
            return None

        return self._schema_registry.get_schema(f"{topic}-value")

