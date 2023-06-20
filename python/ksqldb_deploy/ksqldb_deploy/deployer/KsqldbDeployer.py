import os
import re
from .KsqldbDeployerContext import KsqldbDeployerContext
from .KafkaTopicMetadata import KafkaTopicMetadata
from .KsqldbScript import KsqldbScript
from ksqldb_deploy.util_ksql.KsqldbManager import KsqldbManager
from ksqldb_deploy.util_ksql.KsqldbProperty import KsqldbProperty
from ksqldb_deploy.util_ksql.KsqldbEntity import KsqldbEntity
from ksqldb_deploy.util_kafka.KafkaManager import KafkaManager
from ksqldb_deploy.util_system.FileManager import FileManager
from typing import Dict, List
from urllib.parse import urlparse
from datetime import datetime
from collections import namedtuple
from schema_registry.client.utils import SchemaVersion

KsqldbDeployedChecksum = namedtuple('KsqldbDeployedChecksum', ['relative_path', 'checksum', 'timestamp'])

class KsqldbDeployer():
    KSQLDB_SCHEMA_ID_DIFFERENT_FROM_PROVIDED_REGISTERD_SCHEMA_ID_PATTERN = re.compile("schema id registered is (.*?) ",flags = re.IGNORECASE)
    KSQLDB_SCHEMA_ID_DIFFERENT_FROM_PROVIDED_TOPIC_PATTERN = re.compile("topic: (.*?)\\n",flags = re.IGNORECASE)
    
    def __init__(self, context: KsqldbDeployerContext) -> None:
        super().__init__()

        assert context != None, "context is null"
        assert (context.ksqldb_uri and context.ksqldb_uri.strip()), "ksqldb_uri is invalid"
        self._context = context
        self._scripts_metadata_loaded: bool = False
        self._kafka_scripts_metadata_loaded: bool = False
        self._ksqldb_scripts_checksums_loaded: bool = False

        self._scripts: List[KsqldbScript] = []
        self._entity_script_map: Dict[str, KsqldbScript] = dict()
        self._kafka_topics: Dict[str, KafkaTopicMetadata] = dict()
        self._drop_ksqldb_entities: List[KsqldbEntity] = []
        self._ksqldb_deployed_checksums: Dict[str, KsqldbDeployedChecksum] = dict()

        self._init_ksqldb()
        self._init_kafka()

    def _init_ksqldb(self):
        self._ksqldb_manager: KsqldbManager = KsqldbManager(self._context.ksqldb_uri)
        self._ksqldb_properties: Dict[str, KsqldbProperty] = self._ksqldb_manager.get_server_properties()
        self._ksqldb_dependency_map: Dict[str, KsqldbEntity] = self._ksqldb_manager.get_dependency_map()

        for ksqldb_var_yaml_file in self._context.variable_files:
            self._ksqldb_manager.set_variable_yaml(FileManager().read_yaml(ksqldb_var_yaml_file))

        self._ksqldb_manager.execute(F"""
            CREATE STREAM IF NOT EXISTS ksqldb_{self._context.name}_deployment (
                path string KEY
                ,checksum string
                ,timestamp string
            )
            WITH (
                kafka_topic='ksqldb_{self._context.name}_deployment'
                ,partitions=1
                ,value_format='JSON'
            );

            CREATE TABLE IF NOT EXISTS ksqldb_{self._context.name}_deployment_state
            WITH (
                kafka_topic='ksqldb_{self._context.name}_deployment_state'
                ,partitions=1
                ,value_format='JSON'
            ) AS
                SELECT
                    path
                    ,latest_by_offset(checksum) as checksum
                    ,latest_by_offset(timestamp) as timestamp
                FROM ksqldb_{self._context.name}_deployment
                GROUP BY path
                EMIT CHANGES
            ;
        """)

    def _init_kafka(self):
        schema_registry_property: KsqldbProperty = self.get_ksqldb_property("ksql.schema.registry.url")
        schema_registry_uri = None if schema_registry_property is None else schema_registry_property.value
        if (self._context.schema_registry_url and self._context.schema_registry_url.strip()):
            schema_registry_uri = self._context.schema_registry_url

        kafka_brokers_from_ksqldb = True
        kafka_brokers_property: KsqldbProperty = self.get_ksqldb_property("ksql.streams.bootstrap.servers")
        kafka_brokers = None if kafka_brokers_property is None else kafka_brokers_property.value
        if (self._context.kafka_bootstrap_servers and self._context.kafka_bootstrap_servers.strip()):
            kafka_brokers_from_ksqldb = False
            kafka_brokers = self._context.kafka_bootstrap_servers

        kafka_brokers_no_protocol = []
        for kafka_broker in kafka_brokers.split(','):
            kafka_broker_uri = urlparse(kafka_broker)
            kafka_broker_endpoint = kafka_broker if not kafka_brokers_from_ksqldb else '{uri.netloc}'.format(uri=kafka_broker_uri)
            kafka_brokers_no_protocol.append(kafka_broker_endpoint)

        assert (kafka_brokers and kafka_brokers.strip()), "kafka_brokers is invalid"
        self._kafka_manager: KafkaManager = KafkaManager(bootstrap_servers=kafka_brokers_no_protocol, schema_registry_url=schema_registry_uri)

    def _all_ksqldb_scripts(self) -> List[str]:
        file_manager = FileManager()
        for file in file_manager.find(self._context.base_scripts_path, regex="^.*?\.ksql$"):
            yield file

    def _assign_ksqldb_topic_variables(self, kafka_topic_metadata: KafkaTopicMetadata):
        self._ksqldb_manager.set_variable(F"{kafka_topic_metadata.sanitized_name}_checkpoint", str(kafka_topic_metadata.safe_timestamp))

        if  kafka_topic_metadata.schema is not None:
            self._ksqldb_manager.set_variable(F"{kafka_topic_metadata.sanitized_name}_value_schema_id", str(kafka_topic_metadata.schema.schema_id))
    
    def _load_kafka_topic_metadata(self, kafka_topic: str) -> KafkaTopicMetadata:
        kafka_topic_metadata = KafkaTopicMetadata(kafka_topic)
        kafka_topic_metadata.safe_timestamp = self._kafka_manager.get_topic_last_safe_timestamp(kafka_topic)
        kafka_topic_metadata.schema = self._kafka_manager.get_last_topic_value_schema(kafka_topic)
        self._kafka_topics[kafka_topic] = kafka_topic_metadata
        
        return kafka_topic_metadata
        
    def _ensure_scripts_metadata_loaded(self):
        if not self._scripts_metadata_loaded:
            self.load_scripts_metadata()

    def _ensure_kafka_scripts_metadata_loaded(self):
        if not self._kafka_scripts_metadata_loaded:
            self.load_scripts_kafka_metadata()

    def _ensure_ksqldb_scripts_checksums_loaded(self):
        if not self._ksqldb_scripts_checksums_loaded:
            self.load_ksqldb_scripts_checksums()

    def load_ksqldb_scripts_checksums(self):
        self._ksqldb_scripts_checksums_loaded = False
        self._ksqldb_deployed_checksums: Dict[str, KsqldbDeployedChecksum] = dict()
        for entry in self._ksqldb_manager.query(F"select * from ksqldb_{self._context.name}_deployment_state"):
            self._ksqldb_deployed_checksums[entry['PATH']] = entry['CHECKSUM']
        self._ksqldb_scripts_checksums_loaded = True

    def load_scripts_metadata(self):
        self._ensure_ksqldb_scripts_checksums_loaded()

        self._scripts_metadata_loaded = False
        self._scripts: List[KsqldbScript] = []
        self._entity_script_map: Dict[str, KsqldbScript] = dict()

        for script_path in self._all_ksqldb_scripts():
            file_manager = FileManager()
            ksqldb_script = KsqldbScript()
            ksqldb_script.path = script_path
            ksqldb_script.relative_path = os.path.relpath(script_path, self._context.base_scripts_path)

            ksqldb_script.checksum = file_manager.sha256(script_path)
            ksqldb_script.kafka_topics.extend(self._ksqldb_manager.get_script_kafka_topics(script_file_path=script_path))
            ksqldb_script.ksqldb_entities.extend(self._ksqldb_manager.get_script_ksqldb_entity_names(script_file_path=script_path))
            for entity in ksqldb_script.ksqldb_entities:
                full_scoped_entity = self._ksqldb_dependency_map.get(entity.name)
                if full_scoped_entity is not None:
                    entity.dependencies.extend(full_scoped_entity.dependencies)

            for script_entity in ksqldb_script.ksqldb_entities:
                self._entity_script_map[script_entity.name] = ksqldb_script

            deployed_checksum = self.get_script_deployed_checksum(ksqldb_script.relative_path)
            for script_search in self._context.script:
                if re.match(F".*{script_search}.*", script_path):
                    if (self._context.force) or (ksqldb_script.checksum != deployed_checksum):
                        ksqldb_script.deploy = True

            self._scripts.append(ksqldb_script)

        self._scripts_metadata_loaded = True

    def determine_scripts_deployment_plan(self):
        print(F"    Determining scripts deployment plan ...")

        self._ensure_scripts_metadata_loaded()
        print(F"        Metadata scripts loaded")
        
        self._drop_ksqldb_entities: List[KsqldbEntity] = []
        ksqldb_dropped_entity_names = set()

        print(F"        Going through all deployment scripts ...")
        while True:
            all_scripts_flagged_for_deletion = True
            for script in self.get_deployment_scripts():

                print(F"            Processing script: {script.filename} ...")
                
                for ksqldb_entity in script.ksqldb_entities:
                
                    print(F"                    Processing entity: {ksqldb_entity.name} ...")
                
                    if ksqldb_entity.name in ksqldb_dropped_entity_names:
                        print(F"                    Entity skipped: {ksqldb_entity.name}")
                        continue

                    all_dependencies_deleted = True
                    for dependent_entity_name in ksqldb_entity.dependencies:
                        print(F"                        Processing dependent entity: {dependent_entity_name} ...")
                        if dependent_entity_name in ksqldb_dropped_entity_names:
                            print(F"                        Dependent entity skipped: {dependent_entity_name}")
                            continue

                        all_dependencies_deleted = False
                        all_scripts_flagged_for_deletion = False
                        
                        dependent_script = self.get_script_by_entity_name(dependent_entity_name)
                        dependent_script.deploy = True

                        print(F"                        Dependent entity processed: {dependent_entity_name}")
                    if all_dependencies_deleted:
                        print(F"                    All dependencies deleted for entity: {ksqldb_entity.name}")
                        self._drop_ksqldb_entities.append(ksqldb_entity)
                        ksqldb_dropped_entity_names.add(ksqldb_entity.name)                        

                    print(F"                    Entity processed: {ksqldb_entity.name}")

                print(F"            Script processed: {script.filename}")

            if all_scripts_flagged_for_deletion:
                break

    def load_scripts_kafka_metadata(self, deploy_only: bool = False) -> any:
        self._ensure_scripts_metadata_loaded()

        self.load_scripts_kafka_metadata = False
        self._kafka_topics: Dict[str, KafkaTopicMetadata] = dict()
        for script in self.get_all_scripts():
            if (not deploy_only) or (deploy_only and script.deploy):
                for kafka_topic in self._ksqldb_manager.get_script_kafka_topics(script.path):
                    if kafka_topic in self._kafka_topics:
                        continue
                    
                    self._load_kafka_topic_metadata(kafka_topic=kafka_topic)

        self.load_scripts_kafka_metadata = False
        
    def assign_ksqldb_variables(self):
        for kafka_topic_metadata in self._kafka_topics.values():
            self._assign_ksqldb_topic_variables(kafka_topic_metadata=kafka_topic_metadata)


    def get_ksqldb_property(self, key: str) -> KsqldbProperty or None:
        return self._ksqldb_properties.get(key, None)

    def get_all_scripts(self) -> List[KsqldbScript]:
        return self._scripts

    def get_kafka_metadata(self) -> List[KafkaTopicMetadata] or None:
        return self._kafka_topics.values()

    def get_script_deployed_checksum(self, relative_path: str) -> str or None:
        self._ensure_ksqldb_scripts_checksums_loaded()
        return self._ksqldb_deployed_checksums.get(relative_path)

    def get_script_by_entity_name(self, entity_name: str) -> KsqldbScript or None:
        self._ensure_scripts_metadata_loaded()
        return self._entity_script_map.get(entity_name, None)

    def get_deleting_ksqldb_entities(self) -> List[KsqldbEntity]:
        return self._drop_ksqldb_entities

    def get_deployment_scripts(self) -> List[KsqldbScript]:
        for script in self.get_all_scripts():
            if script.deploy:
                yield script

    def get_variables_script(self) -> str:
        return self._ksqldb_manager.get_variables_script()

    def create_missing_kafka_topics(self):
        self._ensure_scripts_metadata_loaded()
        assert self._context.topic_replicas != None, "topic replicas is null"
        assert self._context.topic_partitions != None, "topic partitions is null"
        
        server_topics = set(self._kafka_manager.get_topics())
        for script in self.get_all_scripts():
            if script.deploy:
                for kafka_topic in script.kafka_topics:
                    if kafka_topic not in server_topics:
                        self._kafka_manager.create_topic(topic_name=kafka_topic,
                                                         partitions=self._context.topic_partitions,        
                                                         replicas=self._context.topic_replicas)
                        server_topics.add(kafka_topic)
                
    def deploy(self, script: KsqldbScript):
        assert script != None, "script is null"
        try:    
            self._ksqldb_manager.deploy(script.path)

            self._ksqldb_manager.execute(F"""
                INSERT INTO ksqldb_{self._context.name}_deployment (path, checksum, timestamp)
                VALUES('{script.relative_path}','{script.checksum}','{datetime.now().isoformat()}');
            """)
        except Exception as e:
            if e.error_code == 40001 and "which is different from provided VALUE_SCHEMA_ID" in str(e.msg):
                try:
                    err_topic = self.KSQLDB_SCHEMA_ID_DIFFERENT_FROM_PROVIDED_TOPIC_PATTERN.findall(e.msg)
                    err_value_schema_id = self.KSQLDB_SCHEMA_ID_DIFFERENT_FROM_PROVIDED_REGISTERD_SCHEMA_ID_PATTERN.findall(e.msg)
                    
                    if (len(err_topic)>0) and (len(err_value_schema_id)>0):
                        kafka_topic = err_topic[0].strip()
                        schema_value_id = int(err_value_schema_id[0])
                        
                        current_kafka_metadata: KafkaTopicMetadata = self._kafka_topics.get(kafka_topic)  
                        if current_kafka_metadata is None:
                            raise e
                        
                        current_kafka_metadata.schema = SchemaVersion(
                                                            F"{kafka_topic}-value"
                                                            ,schema_value_id
                                                            ,self._kafka_manager.get_schema_by_id(schema_id=schema_value_id)
                                                            ,None)
                        
                        if current_kafka_metadata.schema.schema is None:
                            raise e
                        
                        self._kafka_topics[kafka_topic] = current_kafka_metadata
                        self._assign_ksqldb_topic_variables(kafka_topic_metadata=current_kafka_metadata)
                        self.deploy(script)
                    else:
                        raise e
                except Exception as ex:
                    raise e
            else:
                raise e

    def drop(self, ksqldb_entity: KsqldbEntity):
        assert ksqldb_entity != None, "ksqldb entity is null"
        deleting_script = self.get_script_by_entity_name(ksqldb_entity.name)

        if deleting_script is not None:
            self._ksqldb_manager.drop(ksqldb_entity)
            self._ksqldb_manager.execute(F"""
                INSERT INTO ksqldb_{self._context.name}_deployment (path, checksum, timestamp)
                VALUES('{deleting_script.relative_path}', null, '{datetime.now().isoformat()}');
            """)
