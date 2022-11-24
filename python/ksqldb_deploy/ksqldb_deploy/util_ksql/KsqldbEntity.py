from typing import List
from .KsqldbEntityType import KsqldbEntityType
from ksqldb_deploy.utils.ClassUtils import autoRepr

class KsqldbEntity():

    def __init__(self) -> None:
        super().__init__()
        self._dependencies: list[str] = []
        self.name = None
        self.type = None

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def type(self) -> KsqldbEntityType:
        return self._type

    @type.setter
    def type(self, type: KsqldbEntityType) -> None:
        self._type = type

    @type.setter
    def type(self, type: str) -> None:
        if type is None:
            self._type = None
            return

        upper_type = type.upper()
        if upper_type == "TABLE":
            self._type = KsqldbEntityType.TABLE
        elif upper_type == "STREAM":
            self._type = KsqldbEntityType.STREAM
        else:
            self._type = None

    @property
    def dependencies(self) -> List[str]:
        return self._dependencies

    def __str__(self):
        return F"Name: {self.name}, Type: {self.type}, Dependencies: {self.dependencies}"

    def __repr__(self) -> str:
        return autoRepr(self)

    def __str__(self) -> str:
        return self.__repr__()
