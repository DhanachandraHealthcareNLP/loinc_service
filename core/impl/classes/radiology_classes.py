from dataclasses import dataclass
from typing import List, Set
from .core_dto import TextSpan, EntityMentionDto


@dataclass
class RadiologyLoincCodeBean:
    code: str = None
    code_description: str = None
    method: str = None
    system: str = None
    components: Set[str] = None
    text_spans: Set[TextSpan] = None

    def __hash__(self) -> int:
        return hash(self.code)

    def __eq__(self, __value: object) -> bool:
        return self.code == __value.code


@dataclass
class RadiologyLoincPropertyDto:
    text: str = None
    begin: int = None
    end: int = None
    timexValue: str = None


@dataclass
class RadiologyLoincModality(RadiologyLoincPropertyDto):
    pass


@dataclass
class RadiologyLoincPharmaceutical(RadiologyLoincPropertyDto):
    pass


@dataclass
class RadiologyLoincRadiologyroute(RadiologyLoincPropertyDto):
    pass


class RadiologyLoincView(RadiologyLoincPropertyDto):
    pass


@dataclass
class RadiologySystemDto:
    entity_mention_dto: EntityMentionDto = None
    min_distance: int = None
    max_distance: int = None


@dataclass
class RadiologyComponentDto:
    raiology_loinc_modality_list: List[RadiologyLoincModality] = None
    raiology_loinc_pharmaceutical_list: List[RadiologyLoincPharmaceutical] = None
    raiology_loinc_radiologyroute_list: List[RadiologyLoincRadiologyroute] = None
    raiology_loinc_view_list: List[RadiologyLoincView] = None


@dataclass
class RadiologyMethodDto:
    method_entity_mention: EntityMentionDto
    radiology_system_dto_list: List[RadiologySystemDto]
    radiology_component_dto: RadiologyComponentDto


@dataclass
class RadiologyTermMappingTableDto:
    map_id: str = None
    term1: str = None
    term2: str = None
    term3: str = None
    term4: str = None
    term5: str = None
    term6: str = None
    term7: str = None
    code: str = None
    totalTerms: int = 0
