from typing import Any, List, Dict
from ksql import KSQLAPI
from ksql.errors import KSQLError
from ksql.utils import parse_columns
from ksqldb_deploy.util_system.FileManager import FileManager
from .KsqldbEntityType import KsqldbEntityType
from .KsqldbEntity import KsqldbEntity
from .KsqldbProperty import KsqldbProperty
import re
import time
import json

class KsqldbManager():
    REMOVE_MULTILINE_PATTERN = re.compile("\\n|\\r|\\r\\n", flags=re.MULTILINE)
    KSQLDB_SCRIPT_KAFKA_TOPIC_PATTERN = re.compile("kafka_topic.*?\\'(.*?)\\'",flags = re.IGNORECASE)
    KSQLDB_SCRIPT_CLEANUP_PATTERN = re.compile("if not exists|\(.*?\)", flags = re.IGNORECASE)
    KSQLDB_SCRIPT_ENTITY_NAME_PATTERN = re.compile("(stream|table).*?(\w+)", flags= re.IGNORECASE)

    def __init__(self, ksqlapi: str) -> None:
        super().__init__()
        self._client = KSQLAPI(ksqlapi)
        self._client.sa.timeout = 1200
        self._hash_table_exists = None
        self._fileManager = FileManager()
        self._variables: Dict(str,str) = dict()
        self._variable_scripts: List[str] = []

    def get_script_kafka_topics(self, script_file_path: str)-> List[str]:
        script_text = self._fileManager.read(script_file_path)
        matched = self.KSQLDB_SCRIPT_KAFKA_TOPIC_PATTERN.findall(script_text)

        topics = []
        for found in matched:
            topics.append(found)

        return topics

    def get_script_ksqldb_entity_names(self, script_file_path: str)-> List[KsqldbEntity]:
        script_text = self._fileManager.read(script_file_path)
        cleaned = self.KSQLDB_SCRIPT_CLEANUP_PATTERN.sub(" ", self.REMOVE_MULTILINE_PATTERN.sub(" ", script_text))
        matched = self.KSQLDB_SCRIPT_ENTITY_NAME_PATTERN.findall(cleaned)

        ksqldb_entities: Dict[str, KsqldbEntity] = dict()
        for found in matched:
            entity: KsqldbEntity = KsqldbEntity()
            entity.name = found[1].upper()
            entity.type = found[0]
            ksqldb_entities[entity.name] = entity

        return ksqldb_entities.values()

    def set_variable(self, key: str, value: str) -> None:
        self._variables[key] = value

    def set_variable_yaml(self, yaml: Any) -> None:
        for key in yaml:
            self.set_variable(key, str(yaml[key]))

    def get_variable(self, key: str) -> str:
        return self._variables.get(key)
    
    def get_variables_script(self) -> str:
        if len(self._variables) == 0:
            return ""

        script="\r\n".join(self._variable_scripts)
        for variable_key in self._variables.keys():
            script += f"define {variable_key} = '{self._variables[variable_key]}';\r\n"

        return script

    def get_server_properties(self) -> Dict[str, KsqldbProperty]:
        property_map: Dict[str, KsqldbProperty] = dict()
        response = self._client.ksql("show properties;")

        for property in response[0]["properties"]:
            ksqldb_property = KsqldbProperty(property)
            property_map[ksqldb_property.name] = ksqldb_property

        return property_map

    def get_dependency_map(self) -> Dict[str, KsqldbEntity]:
        try:
            dependencies: Dict[str, KsqldbEntity] = dict()

            batches = self._client.ksql(F"list tables extended;list streams extended;")
            for batch in batches:
                for kentity in batch['sourceDescriptions']:
                    entity: KsqldbEntity = KsqldbEntity()
                    entity.name = kentity['name'].upper()
                    entity.type = kentity['type']

                    if entity.type == None:
                        print(F"Unsupported type [{type}] for entity [{entity.name}]. Skipping")
                        continue

                    kentity_dependencies = set()
                    for readQuery in kentity['readQueries']:
                        for sink in readQuery['sinks']:
                            kentity_dependencies.add(sink)

                    for constraint in kentity['sourceConstraints']:
                        kentity_dependencies.add(constraint)

                    entity.dependencies.extend(kentity_dependencies)
                    dependencies[entity.name] = entity

            return dependencies
        except KSQLError as err:
            raise err

    def query(self, ksqldb_query: str) -> Dict[str, any]:
        assert (ksqldb_query and ksqldb_query.strip()), "ksqldb query is invalid"

        retry = True
        while retry:
            header_obj = None
            try:
                response = self._client.query(F"{ksqldb_query}")
                header = next(response)
                header_obj = json.loads(header.replace("[{","{").replace("}}]","}}").replace(",\n",""))["header"]
                column_names = parse_columns(header)

                for row in response:
                    row_obj = json.loads(row.replace("]}}]", "]}}").replace(",\n", "").replace("]\n", ""))
                    column_values = row_obj["row"]["columns"]
                    result = {}
                    for index, column in enumerate(column_values):
                        result[column_names[index]["name"]] = column

                    yield result

            except RuntimeError as e:
                if "stopiteration" in str(e).lower():
                    retry = False
                else:
                    raise e
            except KSQLError as err:
                if err.error_code == 40001:
                    print(F"Query not ready to execute... Retrying after 3 seconds")
                    time.sleep(3)
                    continue
                raise err
            finally:
                if header_obj is not None:
                    self._client.close_query(header_obj["queryId"])


    def execute(self, ksqldb_command: str) -> None:
        retry = True
        while retry:
            try:
                self._client.ksql(F"{self.get_variables_script()} {ksqldb_command} show variables;")
                retry = False
            except KSQLError as err:
                if err.error_code == 50301:
                    print(F"Timed out waiting for a previous command to execute... Retrying after 3 seconds")
                    time.sleep(3)
                    continue
                raise err

    def deploy(self, script_file_path) -> None:
        self.execute(self._fileManager.read(script_file_path))

    def drop(self, ksqldb_entity: KsqldbEntity) -> None:
        retry = True
        while retry:
            script = None
            if ksqldb_entity.type == KsqldbEntityType.TABLE:
                script = F"DROP TABLE IF EXISTS {ksqldb_entity.name}"
            elif ksqldb_entity.type == KsqldbEntityType.STREAM:
                script = F"DROP STREAM IF EXISTS {ksqldb_entity.name}"

            if script is None:
                break

            try:
                self._client.ksql(F"{script};")
                retry = False
            except KSQLError as err:
                if err.error_code == 50301:
                    print(F"Timed out waiting for a previous command to execute... Retrying after 3 seconds")
                    time.sleep(3)
                    continue
                if err.error_code == 40000:
                    print(F"Stream needs to be dropped before it is redeployed")
                    return
                print(F"Error: {err.msg}")
                raise err
