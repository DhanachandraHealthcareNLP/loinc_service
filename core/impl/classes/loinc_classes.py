from dataclasses import dataclass, field
from typing import List, Set
from .core_dto import TextSpan


@dataclass
class LoincComponent:
    text: str = ""
    begin: int = -1
    end: int = -1
    cui_set: List[int] = field(default_factory=list)
    timex_value: str = ""


@dataclass
class LoincCodeBean:
    code: str = ""
    code_desciption: str = ""
    component: str = ""
    property: str = ""
    time_aspct: str = ""
    system: str = ""
    scale_type: str = ""
    method_type: str = ""
    textSpans: Set[TextSpan] = field(default_factory=set)

    def __eq__(self, __value: object) -> bool:
        return list(self.textSpans) == list(__value.textSpans)

    def __hash__(self) -> int:
        return hash(list(self.textSpans)[0])


@dataclass
class LoincUnit:
    text: str = ""
    begin: int = -1
    end: int = -1
    timexValue: str = ""


@dataclass
class LoincSystem(LoincUnit):
    pass


@dataclass
class LoincMethod(LoincUnit):
    pass


if __name__ == "__main__":
    tspan = TextSpan(text="Hihello", begin_offset=20)
    tspan2 = TextSpan(text="name2", begin_offset=10)
    s = set()
    s.add(tspan)
    s.add(tspan2)
    print(s)
