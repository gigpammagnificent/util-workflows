from typing import List

class KsqldbDeployerContext():
    def __init__(self) -> None:
        super().__init__()
        self.name = None
        self.ksqldb_uri = None
        self.schema_registry_url = None
        self.kafka_bootstrap_servers = None
        self.script = [".*"]
        self.base_scripts_path = None
        self.variable_files = []
        self.force = False
        self.topic_partitions = None
        self.topic_replicas = None

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def ksqldb_uri(self) -> str:
        return self._ksqldb_uri

    @ksqldb_uri.setter
    def ksqldb_uri(self, value: str):
        self._ksqldb_uri = value

    @property
    def kafka_bootstrap_servers(self) -> str:
        return self._kafka_bootstrap_servers

    @kafka_bootstrap_servers.setter
    def kafka_bootstrap_servers(self, value: str):
        self._kafka_bootstrap_servers = value

    @property
    def topic_partitions(self) -> int:
        return self._topic_partitions

    @topic_partitions.setter
    def topic_partitions(self, value: int):
        self._topic_partitions = value

    @property
    def topic_replicas(self) -> int:
        return self._topic_replicas

    @topic_replicas.setter
    def topic_replicas(self, value: int):
        self._topic_replicas = value
        
    @property
    def schema_registry_url(self) -> str:
        return self._schema_registry_url

    @schema_registry_url.setter
    def schema_registry_url(self, value: str):
        self._schema_registry_url = value


    @property
    def base_scripts_path(self) -> str:
        return self._base_scripts_path

    @base_scripts_path.setter
    def base_scripts_path(self, value: str):
        self._base_scripts_path = value

    @property
    def force(self) -> bool:
        return self._force

    @force.setter
    def force(self, value: bool):
        self._force = value

    @property
    def variable_files(self) -> List[str]:
        return self._variable_files

    @variable_files.setter
    def variable_files(self, value: List[str]):
        self._variable_files = [] if value is None else value


    @property
    def script(self) -> List[str]:
        return self._script

    @script.setter
    def script(self, value: List[str]):
        self._script = [".*"] if value is None else value

