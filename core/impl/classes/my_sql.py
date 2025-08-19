import time
from dataclasses import dataclass
import os 

import mysql.connector as Cn

from .loinc_classes import LoincCodeBean
from .radiology_classes import RadiologyTermMappingTableDto
from .core_dto import TextSpan
from typing import Set


@dataclass(frozen=True)
class QueryMaster:
    DB_NAME = os.getenv("LOINC_DB_NAME")
    UMLS_DB_NAME = os.getenv("UMLS_DB_NAME")

    unique_system_query = (
        "SELECT distinct `system` FROM "
        + DB_NAME
        + ".loinc WHERE status='ACTIVE' and `system` !=''"
    )
    unique_method_query = (
        "SELECT distinct method_typ FROM "
        + DB_NAME
        + ".Loinc WHERE status='ACTIVE' and method_typ !=''"
    )
    unit_to_property_and_scale_map_query = (
        "SELECT * FROM " + DB_NAME + ".unittopropertyandscalemap where is_active = 1"
    )
    component_to_cui_list_query = (
        "SELECT * FROM " + DB_NAME + ".componenttocuimap where is_active = 1;"
    )
    cui_map_id_query = (
        "Select * from " + DB_NAME + ".radiology_cui_mapping where is_active = 1 and "
    )
    term_map_id_query = (
        "Select * from " + DB_NAME + ".radiology_term_mapping where is_active = 1 and "
    )
    get_loinc_data_using_code = (
        "select * from " + DB_NAME + ".loinc where status='ACTIVE' and loinc_num = ?"
    )
    get_loinc_laboratory_data = (
        "select * from " + DB_NAME + ".loinc where status='ACTIVE'"
    )

    get_all_radiology_cui = (
        "Select * from " + DB_NAME + ".radiology_cui_map where is_active = 1"
    )

    get_text_of_cui = (
        "Select distinct text From " + UMLS_DB_NAME + ".umls_test1 where cui = ?"
    )


class QueryMySQL:
    def __init__(self, connection) -> None:
        self.query_master = QueryMaster()
        self.statement = connection.cursor(dictionary=True)
        self.ps_get_umls_text_from_cui = self.query_master.get_text_of_cui
        self.ps_get_loinc_data_from_code = self.query_master.get_loinc_data_using_code

    def get_loinc_codes(self, query: str):
        start = time.time()
        self.statement.execute(query)
        end = time.time()

        loinc_code_beans = []
        for resultSet in self.statement:
            code = resultSet.get("loinc_num")
            code_desc = resultSet.get("long_common_name")
            component = resultSet.get("component")
            property = resultSet.get("property")
            time_aspect = resultSet.get("time_aspct")
            system = resultSet.get("system")
            scale_type = resultSet.get("scale_typ")
            method_type = resultSet.get("method_typ")

            loinc_code_bean = LoincCodeBean(
                code=code,
                code_desciption=code_desc,
                component=component,
                scale_type=scale_type,
                method_type=method_type,
                property=property,
                time_aspct=time_aspect,
                system=system,
            )
            loinc_code_beans.append(loinc_code_bean)

        return loinc_code_beans

    def check_bilateral_in_text(self, cui: int):
        self.ps_get_umls_text_from_cui.replace("?", str(cui))
        start = time.time()
        self.statement.execute(self.ps_get_umls_text_from_cui)
        end = time.time()

        is_bilateral_found = False
        for res in self.statement:
            text = res.get("text").lower()

            if (
                "bilateral" in text
                or "bilaterally" in text
                or "both" in text
                or "b/l" in text
            ):
                is_bilateral_found = True
                break

        return is_bilateral_found

    def get_radiology_cui_map_id(self, query: int):
        start = time.time()
        self.statement.execute(query)
        end = time.time()

        map_id_set = []
        for result_set in self.statement:
            map_id = result_set.get("map_id")
            map_id_set.append(map_id)

        return map_id_set

    def get_radiology_term_mapping(self, query):
        start = time.time()
        self.statement.execute(query)
        end = time.time()

        map_id_set = []

        for result_set in self.statement:
            total_term = 0

            map_id = result_set.get("map_id")

            term1 = result_set.get("term1")
            if term1 is not None:
                total_term += 1
            term2 = result_set.get("term2")
            if term2 is not None:
                total_term += 1
            term3 = result_set.get("term3")
            if term3 is not None:
                total_term += 1
            term4 = result_set.get("term4")
            if term4 is not None:
                total_term += 1
            term5 = result_set.get("term5")
            if term5 is not None:
                total_term += 1
            term6 = result_set.get("term6")
            if term6 is not None:
                total_term += 1
            term7 = result_set.get("term7")
            if term7 is not None:
                total_term += 1

            code = result_set.get("code")

            dto = RadiologyTermMappingTableDto(
                map_id=map_id,
                term1=term1,
                term2=term2,
                term3=term3,
                term4=term4,
                term5=term5,
                term6=term6,
                term7=term7,
                code=code,
                totalTerms=total_term,
            )

            map_id_set.append(dto)

        return map_id_set

    def get_loinc_master_data_from_code(self, code: str, text_span: Set[TextSpan]):
        self.ps_get_loinc_data_from_code = self.ps_get_loinc_data_from_code.replace("?", code)
        start = time.time()
        self.statement.execute(self.ps_get_loinc_data_from_code)
        end = time.time()
        loinc_code_bean = None 
        for resultSet in self.statement:
            codeDescription = resultSet.get("long_common_name")
            component = resultSet.get("component")
            property = resultSet.get("property")
            time_aspct = resultSet.get("time_aspct")
            system = resultSet.get("system")
            scale_typ = resultSet.get("scale_typ")
            method_typ = resultSet.get("method_typ")

            loinc_code_bean = LoincCodeBean(
                code=code,
                code_desciption=codeDescription,
                component=component,
                property=property,
                time_aspct=time_aspct,
                system=system,
                scale_type=scale_typ,
                method_type=method_typ,
                textSpans=text_span,
            )

        return loinc_code_bean


if __name__ == "__main__":
    query_sql = QueryMySQL()

    query = "select * from loinc.radiology_term_mapping where term1='W contrast'"

    res = query_sql.get_radiology_term_mapping(query=query)

    print(res[0])
