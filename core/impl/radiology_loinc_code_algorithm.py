import copy
import logging
from typing import Dict, List, Set

from .classes.core_dto import EntityMentionDto, TextSpan
from .classes.my_sql import QueryMySQL
from .classes.radiology_classes import (RadiologyComponentDto,
                                        RadiologyLoincCodeBean,
                                        RadiologyLoincPropertyDto,
                                        RadiologyMethodDto,
                                        RadiologyTermMappingTableDto)
from .loinc_rule_based_filter import LoincRuleBasedFilter


class RadiologyLoincCodeAlgorithm:
    def __init__(self, connection) -> None:
        self.query_my_sql = QueryMySQL(connection=connection)
        self.loinc_rule_based_filter = LoincRuleBasedFilter()

    def get_combination(self, lisOfList):
        allCombinationList = []
        self.generateValues(lisOfList, "", allCombinationList)
        return allCombinationList

    def generateValues(
        self, outerList: List[List[int]], outPut: str, allCombinationList: List[str]
    ):
        lst = next(iter(outerList))
        for s in lst:
            newOuter = copy.deepcopy(outerList)
            if lst in outerList:
                newOuter.remove(lst)
            if len(outerList) > 1:
                self.generateValues(
                    newOuter, (outPut + " " + str(s)).strip(), allCombinationList
                )
            else:
                lemmaValues = (outPut + " " + str(s)).strip()
                allCombinationList.append(lemmaValues)

    def get_radiology_loinc_code(
        self, radiology_method_dto: RadiologyMethodDto
    ) -> Set[RadiologyLoincCodeBean]:
        
        logging.info(f"==> Inside get_radiology_loinc_code")
        method_entity_mention = radiology_method_dto.method_entity_mention
        method_cui_list = method_entity_mention.cui_set

        radiology_system_dto_list = radiology_method_dto.radiology_system_dto_list

        system_entity_mention = None
        cui_map_id_list = []
        radiology_loinc_code_list = set()

        for radiology_system_dto in radiology_system_dto_list:

            logging.info(f"==> For system Dto : {radiology_system_dto}")
            system_cui_list = self.loinc_rule_based_filter.filter_cuis_of_bilateral(
                radiology_system_dto.entity_mention_dto, self.query_my_sql
            )
            logging.info(f"==> System list after filtering : {system_cui_list}")
            outer_cui_list = []
            outer_cui_list.append(method_cui_list)
            outer_cui_list.append(system_cui_list)

            combination_ofcui_list = self.get_combination(outer_cui_list)
            logging.info(f"==> Combination of Cui List : {combination_ofcui_list}")

            for cui_pair in combination_ofcui_list:
                cui_list = []
                for single_cui in cui_pair.split(" "):
                    cui_list.append(int(single_cui))

                cui_map_id_list = self.get_map_id_from_radiology_cui_mapping(cui_list)
                if len(cui_map_id_list) != 0:
                    system_entity_mention = radiology_system_dto.entity_mention_dto
                    break

            if len(cui_map_id_list) != 0:
                break

        if len(cui_map_id_list) != 0:
            radiology_component_dto = radiology_method_dto.radiology_component_dto
            radiology_loinc_code_list = self.get_radiology_codes(
                cui_map_id_list,
                radiology_component_dto,
                method_entity_mention,
                system_entity_mention,
            )

        return radiology_loinc_code_list

    def get_map_id_from_radiology_cui_mapping(self, cui_list: List[int]):
        length = len(cui_list)
        cui_string = ""
        for cui in cui_list:
            cui_string += str(cui) + ", "
        cui_string = cui_string[0 : len(cui_string) - 2]

        query = ""
        i = 1
        for _ in range(1, length + 1):
            query += "cui" + str(i) + " in (" + cui_string + ") and "
            i += 1

        query = (
            self.query_my_sql.query_master.cui_map_id_query
            + query
            + "cui"
            + str(i)
            + " is null"
        )

        cui_map_id_list = self.query_my_sql.get_radiology_cui_map_id(query)

        return cui_map_id_list

    def get_radiology_codes(
        self,
        cui_map_id_list: List[str],
        radiology_component_dto: RadiologyComponentDto,
        method_entity_mention: EntityMentionDto,
        system_entity_mention: EntityMentionDto,
    ) -> Set[RadiologyLoincCodeBean]:
        radiology_loinc_code_list = set()

        logging.info(f"==> Inside get_radiology_codes")
        try:
            radiology_term_mapping_row_set: List[
                RadiologyTermMappingTableDto
            ] = self.get_all_term_mapping_from_cui_mapping(cui_map_id_list)
            logging.info(f"==> radiology_term_mapping_row_set from CUI set: {radiology_term_mapping_row_set}")
            
            all_components = self.get_all_components(radiology_component_dto)
            logging.info(f"==> All components: {all_components}")

            probable_outptu_dto: List[RadiologyTermMappingTableDto] = []
            cui_map_id_whiche_arefound_in_term_mapping = set()

            threshold_value = 1
            total_component_found = len(all_components)
            globalmiss_count = 9999999999


            for table_dto in radiology_term_mapping_row_set:
                logging.info(f"==> Searching for Table Dto : {table_dto} in radiology_term_mapping_row_set")
                cui_map_id_whiche_arefound_in_term_mapping.add(table_dto.map_id)
                total_term_in_raw = table_dto.totalTerms

                if total_component_found == 0 and total_term_in_raw == 0:
                    probable_outptu_dto.clear()
                    probable_outptu_dto.append(table_dto)
                    break

                match_count = self.get_total_number_of_matched_term(
                    table_dto, all_components
                )
                logging.info(f"==> Match count : {match_count}")

                miss_count = total_term_in_raw - match_count
                logging.info(f"==> Miss count : {miss_count}")

                if (
                    match_count == total_term_in_raw
                    and total_term_in_raw == total_component_found
                ):
                    probable_outptu_dto.clear()
                    probable_outptu_dto.append(table_dto)
                    break

                if match_count == threshold_value:
                    if miss_count < globalmiss_count:
                        probable_outptu_dto.clear()
                        probable_outptu_dto.append(table_dto)
                        globalmiss_count = miss_count

                elif match_count > threshold_value:
                    probable_outptu_dto.clear()
                    probable_outptu_dto.append(table_dto)
                    threshold_value = match_count
                    globalmiss_count = miss_count

            if len(probable_outptu_dto) == 0 or probable_outptu_dto == []:
                for cui_map_id in cui_map_id_list:
                    if cui_map_id in cui_map_id_whiche_arefound_in_term_mapping:
                        continue
                    code = cui_map_id.replace("-id", "")
                    evidence_list: Set[TextSpan] = set()
                    self.get_text_span_from_entity_mention_dto(
                        method_entity_mention, evidence_list
                    )
                    self.get_text_span_from_entity_mention_dto(
                        system_entity_mention, evidence_list
                    )

                    code_bean = RadiologyLoincCodeBean(
                        code=code, text_spans=evidence_list
                    )
                    radiology_loinc_code_list.add(code_bean)

            else:
                for dto in probable_outptu_dto:
                    code = dto.code
                    evidenceList: Set[TextSpan] = set()
                    evidenceList = self.get_text_span(
                        evidenceList,
                        dto,
                        all_components,
                        method_entity_mention,
                        system_entity_mention,
                    )
                    code_bean = RadiologyLoincCodeBean(
                        code=code, text_spans=evidence_list
                    )
                    radiology_loinc_code_list.add(code_bean)

        except Exception as err:
            print(err)

        logging.info(f"==> Returning loinc code list : {radiology_loinc_code_list}")
        return radiology_loinc_code_list

    def get_all_term_mapping_from_cui_mapping(
        self, cui_map_id_list: List[str]
    ) -> List[RadiologyTermMappingTableDto]:
        cui_map_string = "("
        for cui in cui_map_id_list:
            cui_map_string += "'" + cui + "', "

        query = (
            self.query_my_sql.query_master.term_map_id_query
            + " map_id in "
            + cui_map_string[0 : len(cui_map_string) - 2]
            + ")"
        )

        radiology_term_mapping_row_set = self.query_my_sql.get_radiology_term_mapping(
            query
        )

        return radiology_term_mapping_row_set

    def get_all_components(
        self, component_dto: RadiologyComponentDto
    ) -> Dict[str, RadiologyLoincPropertyDto]:
        all_components = dict()

        modality = component_dto.raiology_loinc_modality_list
        view = component_dto.raiology_loinc_view_list
        pharmaceutical = component_dto.raiology_loinc_pharmaceutical_list
        radiology_route = component_dto.raiology_loinc_radiologyroute_list

        if modality is not None:
            for mod in modality:
                all_components.update({mod.timexValue.lower(): mod})

        if view is not None:
            for mod in view:
                all_components.update({mod.timexValue.lower(): mod})

        if pharmaceutical is not None:
            for mod in pharmaceutical:
                all_components.update({mod.timexValue.lower(): mod})

        if radiology_route is not None:
            for mod in radiology_route:
                all_components.update({mod.timexValue.lower(): mod})

        return all_components

    def get_total_number_of_matched_term(
        self,
        table_dto: RadiologyTermMappingTableDto,
        all_components: Dict[str, RadiologyLoincPropertyDto],
    ) -> int:
        match_count = 0
        match_count += self.check_term_in_table(table_dto.term1, all_components)
        match_count += self.check_term_in_table(table_dto.term2, all_components)
        match_count += self.check_term_in_table(table_dto.term3, all_components)
        match_count += self.check_term_in_table(table_dto.term4, all_components)
        match_count += self.check_term_in_table(table_dto.term5, all_components)
        match_count += self.check_term_in_table(table_dto.term6, all_components)
        match_count += self.check_term_in_table(table_dto.term7, all_components)

        return match_count

    def check_term_in_table(
        self, term: str, all_components: Dict[str, RadiologyLoincPropertyDto]
    ) -> int:
        if term is not None:
            if term.lower() in all_components:
                return 1
        return 0

    def get_text_span_from_entity_mention_dto(
        self, entitymention_dto: EntityMentionDto, evidence_list: Set[TextSpan]
    ):
        i = 0
        text_set = entitymention_dto.text_set

        for beg in entitymention_dto.begin_set:
            span = TextSpan(begin_offset=beg, text=text_set[i])
            evidence_list.add(span)
            i += 1

    def get_text_span(
        self,
        evidence_list: Set[TextSpan],
        dto: RadiologyTermMappingTableDto,
        all_components: Dict[str, RadiologyLoincPropertyDto],
        method_entity_mention: EntityMentionDto,
        system_entity_mention: EntityMentionDto,
    ) -> Set[TextSpan]:
        self.add_valid_evidecne_to_set(dto.term1, evidence_list, all_components)
        self.add_valid_evidecne_to_set(dto.term2, evidence_list, all_components)
        self.add_valid_evidecne_to_set(dto.term3, evidence_list, all_components)
        self.add_valid_evidecne_to_set(dto.term4, evidence_list, all_components)
        self.add_valid_evidecne_to_set(dto.term5, evidence_list, all_components)
        self.add_valid_evidecne_to_set(dto.term6, evidence_list, all_components)
        self.add_valid_evidecne_to_set(dto.term7, evidence_list, all_components)

        self.get_text_span_from_entity_mention_dto(method_entity_mention, evidence_list)
        self.get_text_span_from_entity_mention_dto(system_entity_mention, evidence_list)

        return evidence_list

    def add_valid_evidecne_to_set(
        self,
        term: str,
        evidence_list: Set[TextSpan],
        all_components: Dict[str, RadiologyLoincPropertyDto],
    ):
        if term is not None:
            if term.lower() in all_components:
                dto = all_components.get(term.lower())

                span = TextSpan(begin_offset=dto.begin, text=dto.text)
                evidence_list.add(span)


if __name__ == "__main__":
    radio = RadiologyLoincCodeAlgorithm()
