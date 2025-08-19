from dataclasses import dataclass
from typing import List, Set

from .loinc_classes import LoincMethod, LoincSystem


@dataclass
class LaboratoryLoincCodeCacheDto:
    present_systems: Set[str] = None
    present_methods: Set[str] = None
    property: str = None
    component_set: Set[str] = None
    time: str = None
    scale: str = None

    def __hash__(self) -> int:
        prime = 31
        result = 1

        result = prime * result + (
            0 if self.component_set is None else id(self.component_set)
        )
        result = prime * result + (
            0 if self.present_methods is None else id(self.present_methods)
        )
        result = prime * result + (
            0 if self.present_systems is None else id(self.present_systems)
        )
        result = prime * result + (0 if self.property is None else hash(self.property))
        result = prime * result + (0 if self.scale is None else hash(self.scale))
        result = prime * result + (0 if self.time is None else hash(self.time))

        return result

    def __eq__(self, obj: object) -> bool:
        if self == obj:
            return True
        if obj == None:
            return False
        if self.__class__ != obj.__class__:
            return False

        other = LaboratoryLoincCodeCacheDto()
        if self.component_set is None:
            if other.component_set is not None:
                return False
        elif self.component_set != other.component_set:
            return False

        if self.present_methods is None:
            if other.present_methods is not None:
                return False
        elif self.present_methods != other.present_methods:
            return False

        if self.present_systems is None:
            if other.present_systems is not None:
                return False
        elif self.present_systems != other.present_systems:
            return False

        if self.property is None:
            if other.property is not None:
                return False
        elif self.property != other.property:
            return False

        if self.time is None:
            if other.time is not None:
                return False
        elif self.time != other.time:
            return False

        if self.scale is None:
            if other.scale is not None:
                return False
        elif self.scale != other.scale:
            return False

        return True


class LaboratoryLoincCodeCache:
    def __init__(self) -> None:
        self.max_cache_limit = 50000
        self.cache_map = dict()

    def check_cache_is_available(
        self, component_set, property, present_systems, time, scale, present_methods
    ):
        cache_dto = self.get_laboratory_loinc_code_cache_dto(
            component_set, property, present_systems, time, scale, present_methods
        )
        if cache_dto in self.cache_map.keys():
            return cache_dto.get(cache_dto)

    def get_laboratory_loinc_code_cache_dto(
        self,
        component_set: Set[str],
        property: str,
        present_systems: List[LoincSystem],
        time: str,
        scale: str,
        present_methods: List[LoincMethod],
    ):
        cache_dto = LaboratoryLoincCodeCacheDto()

        if component_set is not None:
            component_set = self.convert_set_data_to_lower(component_set)
            cache_dto.component_set = component_set

        if property is not None:
            cache_dto.property = property

        if scale is not None:
            cache_dto.scale = scale

        if time is not None:
            cache_dto.time = time

        present_methods_set = set()
        present_systems_set = set()

        if present_systems is not None:
            for system in present_systems:
                present_systems_set.add(system.timexValue.lower())

        if present_methods is not None:
            for method in present_methods:
                present_methods_set.add(method.timexValue.lower())

        cache_dto.present_methods = present_methods_set
        cache_dto.present_systems = present_systems

        return cache_dto

    def convert_set_data_to_lower(self, component_set: Set[str]):
        return set(map(lambda x: x.lower(), component_set))

    def add_into_cache(
        self,
        loinc_code_beans,
        component_set,
        property,
        present_systems,
        time,
        scale,
        present_methods,
    ):
        if len(self.cache_map) <= self.max_cache_limit:
            cache_dto = self.get_laboratory_loinc_code_cache_dto(
                component_set, property, present_systems, time, scale, present_methods
            )
            self.cache_map.update({cache_dto: loinc_code_beans})
