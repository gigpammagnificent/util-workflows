import os
from typing import List
from ksqldb_deploy.util_ksql.KsqldbEntity import  KsqldbEntity
from ksqldb_deploy.utils.ClassUtils import autoRepr

class KsqldbScript():

    def __init__(self) -> None:
        super().__init__()
        self.path = None
        self.relative_path = None
        self.deploy = False
        self.checksum = None
        self._kafka_topics: List[str] = []
        self._ksqldb_entities: List[KsqldbEntity] = []

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, value: str):
        self._path = value

    @property
    def relative_path(self) -> str:
        return self._relative_path

    @relative_path.setter
    def relative_path(self, value: str):
        self._relative_path = value

    @property
    def filename(self) -> str:
        return None if self.path is None else os.path.basename(self.path)

    @property
    def deploy(self) -> bool:
        return self._deploy

    @deploy.setter
    def deploy(self, value: bool):
        self._deploy = value


    @property
    def checksum(self) -> str:
        return self._checksum

    @checksum.setter
    def checksum(self, value: str):
        self._checksum = value

    @property
    def kafka_topics(self) -> List[str]:
        return self._kafka_topics

    @property
    def ksqldb_entities(self) -> List[KsqldbEntity]:
        return self._ksqldb_entities


    def __repr__(self) -> str:
        return autoRepr(self)

    def __str__(self) -> str:
        return self.__repr__()
