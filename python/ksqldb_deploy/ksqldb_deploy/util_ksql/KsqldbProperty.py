from typing import List

class KsqldbProperty():

    def __init__(self) -> None:
        super().__init__()

    def __init__(self, struct: dict) -> None:
        super().__init__()
        self.name = struct['name']
        self.scope = struct['scope']
        self.value = struct['value']
        self.editable = struct['editable']
        self.level = struct['level']

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value


    @property
    def scope(self) -> str:
        return self._scope

    @scope.setter
    def scope(self, value: str) -> None:
        self._scope = value


    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        self._value = value


    @property
    def editable(self) -> bool:
        return self._editable

    @editable.setter
    def editable(self, value: bool) -> None:
        self._editable = value


    @property
    def level(self) -> str:
        return self._level

    @level.setter
    def level(self, value: str) -> None:
        self._level = value
