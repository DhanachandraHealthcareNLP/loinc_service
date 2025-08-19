from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Span:
    begin: int = None
    end: int = None
    address_id: int = None

    def __hash__(self) -> int:
        prime = 31
        result = 1
        result = (
            prime * result
            if self.address_id is None
            else prime * result + self.address_id
        )
        result = prime * result if self.begin is None else prime * result + self.begin
        result = prime * result if self.end is None else prime * result + self.end

        return result

    def __eq__(self, __value: object) -> bool:
        return self.begin == __value.begin and self.end == __value.end

    def is_overlap(self, oth_begin, oth_end) -> bool:
        if (self.begin < oth_begin and oth_end < self.end) and (oth_end > self.end):
            return True
        if (oth_begin < self.begin and self.begin < oth_end) and (self.end > oth_end):
            return True
        return False

    def is_cover(self, othBegin, othEnd):
        return (self.begin <= othBegin) and (othEnd <= self.end)


@dataclass
class TextSpan:
    text: str = None
    begin_offset: int = None

    def __repr__(self) -> str:
        return (
            "TextSpan [text="
            + self.text
            + ", beginOffset="
            + str(self.begin_offset)
            + "]"
        )

    def __hash__(self) -> int:
        return hash(self.begin_offset)

    def __eq__(self, __value: object) -> bool:
        return self.begin_offset == __value.begin_offset


@dataclass
class CRFEntityMention:
    id: int = None

    begin: int = None
    end: int = None
    entity_type: str = None

    cui_list: List[str] = None
    tui_list: List[str] = None
    sui_list: List[str] = None

    confidence: float = None
    token_list: List[int] = None
    negation: str = None
    status: str = None

    unit_list: List[int] = None
    freq_list: List[int] = None
    dosage_list: List[int] = None
    form_list: List[int] = None
    strength_list: List[int] = None

    method_list: List[int] = None
    system_list: List[int] = None
    value_list: List[int] = None
    modality_list: List[int] = None

    view_list: List[int] = None
    pharmaceutical_list: List[int] = None
    radiologyroute_list: List[int] = None


@dataclass
class EntityMentionDto:
    id: int = None
    begin_set: List[int] = None
    end_set: List[int] = None
    text_set: List[str] = None
    cui_set: List[int] = None
    tui_set: List[str] = None
    sui_set: List[int] = None
    possible_entity_type_set: List = None

    def __eq__(self, __value: object) -> bool:
        self.id = __value.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class ModalityToken:
    begin = None
    end = None
    covered_text = None
    timex_value = None


@dataclass
class ViewToken(ModalityToken):
    pass


@dataclass
class PharmaceuticalToken(ModalityToken):
    pass


@dataclass
class RadiologyrouteToken(ModalityToken):
    pass


@dataclass
class Sentence:
    begin: int = None
    end: int = None
    sentence_num: int = None
    covered_text: str = None

    def __eq__(self, __value: object) -> bool:
        return self.begin == __value.begin and self.end == __value.end

    def __hash__(self) -> int:
        return hash(self.begin)


class AttributeLoader:
    def __init__(self, cDoc: Dict) -> None:
        self.cDoc = cDoc
        self.attr_ann_map = self.load_annotation_from_cdoc(cDoc)

    def load_annotation_from_cdoc(self, cDoc: Dict):
        if "tokens" in cDoc.keys():
            attr_ann_map = dict()

            for it in cDoc["tokens"]:
                attr_ann_map[int(it["id"])] = it

            return attr_ann_map
        else:
            print("ERROR: Line 155 in AttributeLoader : Key 'contextTokens' not found")

    def get_attribute(self, id: int):
        return self.attr_ann_map.get(id)


if __name__ == "__main__":
    s1 = Span(10, 20)
    s2 = Span(30, 40)

    d = dict()
    d[s1] = "qjfnijnfjsaf"
    d[s2] = "wfiamfqnf"

    s3 = Span(10, 20)

    print(s3 in d)
