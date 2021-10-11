from typing import Optional, Any, cast
from pdm.core import Project

def _get_config_value(config: dict[str, Any], *keys: str) -> Optional[Any]:
    while len(keys) > 1:
        front: str = keys[0]
        if front in config.keys():
            config = cast(dict[str, Any], config[front])
            keys = tuple(keys[1:])
        else:
            return None
    
    front: str = keys[0]
    return None if front not in config.keys() else config[front]

def _set_config_value(config: dict[str, Any], value: Any, *keys: str) -> None:
    while len(keys) > 1:
        front: str = keys[0]
        if front not in config.keys():
            config[front] = {}
        keys = tuple(keys[1:])
    
    front: str = keys[0]
    config[front] = value

class Config:
    def __init__(self, project: Project) -> None:
        self.__project = project

    def get_pyproject_value(self, *keys: str) -> Optional[Any]:
        config: dict[str, Any] = self.__project.pyproject
        return _get_config_value(config, *keys)

    def set_pyproject_value(self, value: Any, *keys: str) -> None:
        config: dict[str, Any] = self.__project.pyproject
        _set_config_value(config, value, *keys)
            
