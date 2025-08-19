import copy
import logging
from typing import Dict, List, Set

from .classes.core_dto import *
from .classes.radiology_classes import *
from .radiology_loinc_code_algorithm import RadiologyLoincCodeAlgorithm


class RadiologyLoincCodeService:
    def __init__(self, connection, attribute_loader) -> None:
        self.connection = connection
        self.method_quilified_cui_list = set()
        self.radiology_loinc_algo = RadiologyLoincCodeAlgorithm(
            connection=self.connection
        )
        self.attribute_loader: AttributeLoader = attribute_loader

    def init_radiology_loinc_service(self):
        try:
            self.get_method_qualified_cui_list()
        except Exception as err:
            print(err)

    def get_method_qualified_cui_list(self):
        all_cuis = "41618,220934,1456803,1875843,2368378,243032,162481,34571,43309,1306645,1962945,3244296,24485,1552358,16356,40405,1552357,16356,34571,43309,1306645,1962945,3244296,10000553,10001564,34606,34607,2368359,3665374,10001564,34606,34607,2368359,3665374,40399,24671,260913,24671,260913,729296,1514967,40404,16356,16356,3463807,1510486,40405,1552357,31001,1536105,1441535,34571,43309,1306645,1962945,3244296,16356,16356,10000553,24487,34571,43309,1306645,1962945,3244296,729296,1514967,32743,376335,40405,1552357,31001,1536105,1441535,24671,260913,10002881,10001564,34606,34607,2368359,3665374,40399,40405,1552357,41618,220934,1456803,1875843,2368378,2748260,2367013,40405,1552357,11321,41618,220934,1456803,1875843,2368378,24671,260913,32743,31001,40405,1552357,1536105,1441535,40405,1552357,31001,1536105,1441535"
        for single_cui in all_cuis.split(","):
            self.method_quilified_cui_list.add(int(single_cui))

    def find_radiology_loinc_code(
        self,
        sent: Sentence,
        entity_mention_dto_set: Set[EntityMentionDto],
        crf_beg_end_to_crf_mention: Dict[Span, CRFEntityMention],
        radiology_loinc_code_bean_set: Set[RadiologyLoincCodeBean],
    ) -> Set[RadiologyLoincCodeBean]:
        
        # Sent should contain sentence begin and end and other details
        for entity_mention_dto in entity_mention_dto_set:
            logging.info(f"==> Checking for entity: {entity_mention_dto}")

            if self.check_method_is_valid(entity_mention_dto):

                em_begin_list = entity_mention_dto.begin_set
                em_end_list = entity_mention_dto.end_set

                crf_entity_mention = None
                start = 0
                for begin in em_begin_list:
                    end = em_end_list[start]
                    emspan = Span(begin=begin, end=end)
                    crf_entity_mention = (
                        self.get_crf_entity_mention_from_entity_mention(
                            emspan, crf_beg_end_to_crf_mention
                        )
                    )

                    if crf_entity_mention is not None:
                        break
                    start += 1

                logging.info(f"==> Begin list: {em_begin_list}, End list: {em_end_list}, CRF_Entity: {crf_entity_mention}")

                radiology_system_dto_list = (
                    self.get_all_anatomical_structure_with_distance(
                        sent, entity_mention_dto_set, entity_mention_dto
                    )
                )

                logging.info(f"==> Radiology System Dto List : {radiology_system_dto_list}")

                radiology_component_dto = RadiologyComponentDto()
                if crf_entity_mention is not None:
                    radiology_component_dto = self.get_component_from_crf(
                        crf_entity_mention
                    )

                    logging.info(f"==> Radiology Component Dto List : {radiology_component_dto}")

                method_dto = RadiologyMethodDto(
                    method_entity_mention=entity_mention_dto,
                    radiology_component_dto=radiology_component_dto,
                    radiology_system_dto_list=radiology_system_dto_list,
                )

                logging.info(f"==> Method Dto : {method_dto}. Finding the radiology code.")
                radiology_loinc_code_bean_set.update(
                    self.radiology_loinc_algo.get_radiology_loinc_code(method_dto)
                )

        return radiology_loinc_code_bean_set

    def get_crf_entity_mention_from_entity_mention(
        self, em_span: Span, crf_beg_end_to_crf_mention: Dict[Span, CRFEntityMention]
    ):
        if em_span in crf_beg_end_to_crf_mention.keys():
            return crf_beg_end_to_crf_mention.get(em_span)

        for span in crf_beg_end_to_crf_mention.keys():
            if span.is_cover(em_span.begin, em_span.end) or em_span.is_cover(
                span.begin, span.end
            ):
                return crf_beg_end_to_crf_mention.get(span)

            if span.is_cover(em_span.begin, em_span.end):
                crf_beg_end_to_crf_mention.get(span)

        return None

    def get_all_anatomical_structure_with_distance(
        self,
        sent: Sentence,
        entity_mention_dto_set: Set[EntityMentionDto],
        entity_mention_dto: EntityMentionDto,
    ) -> List[RadiologySystemDto]:
        radiology_system_dto_tree_set = list()
        sent_begin = sent.begin
        sentence = sent.covered_text

        begin_list = entity_mention_dto.begin_set
        end_list = entity_mention_dto.end_set

        for sub_dto in entity_mention_dto_set:
            if sub_dto == entity_mention_dto:
                continue
            entit_type_list = sub_dto.possible_entity_type_set
            if "ANATOMICAL_STRUCTURE" in entit_type_list:
                sub_begin_list = sub_dto.begin_set
                sub_end_list = sub_dto.end_set

                min_distance = 999999999
                max_distance = 0

                i = 0

                for begin in begin_list:
                    end = end_list[i]
                    isub = 0
                    for sub_begin in sub_begin_list:
                        sub_end = sub_end_list[isub]

                        if sub_end < begin:
                            between_text = sentence[
                                sub_end - sent_begin : begin - sent_begin
                            ].strip()

                            between_tokens = len(between_text.split(" "))
                            if between_tokens < min_distance:
                                min_distance = between_tokens
                            if between_tokens > max_distance:
                                max_distance = between_tokens

                        elif sub_begin > end:
                            between_text = sentence[
                                end - sent_begin : sub_begin - sent_begin
                            ].strip()
                            between_tokens = len(between_text.split(" "))
                            if between_tokens < min_distance:
                                min_distance = between_tokens
                            if between_tokens > max_distance:
                                max_distance = between_tokens

                        else:
                            min_distance = 0

                        isub += 1

                    i += 1

                radiologySystemDto = RadiologySystemDto(
                    entity_mention_dto=sub_dto,
                    max_distance=max_distance,
                    min_distance=min_distance,
                )

                radiology_system_dto_tree_set.append(radiologySystemDto)

        # TODO : Check hashing in RadiologySystemDto
        return radiology_system_dto_tree_set

    def check_method_is_valid(self, entity_mention_dto: EntityMentionDto):
        cui_list = entity_mention_dto.cui_set
        for cui in cui_list:
            if cui in self.method_quilified_cui_list:
                logging.info(f"==> The entity {entity_mention_dto} is valid !")
                return True
            
        logging.info(f"==> The entity {entity_mention_dto} is NOT valid, returning.")
        return False

    def get_component_from_crf(
        self, crf_entity: CRFEntityMention
    ) -> RadiologyComponentDto:
        radiology_component_dto = RadiologyComponentDto()

        modality_bean_list = None
        modality_set = crf_entity.modality_list

        temp_delete_modality = ""
        if modality_set is not None:
            modality_bean_list = []
            i = 0
            for modality_id_single in modality_set:
                token = self.attribute_loader.get_attribute(modality_id_single)

                bean = RadiologyLoincModality(
                    begin=int(token["begin"]),
                    end=int(token["end"]),
                    text=token["text"],
                    timexValue=token["text"],
                )

                modality_bean_list.append(bean)
                temp_delete_modality += token["text"] + "_MODALITY_"

        view_bean_list = None
        view_set = crf_entity.view_list

        temp_delete_view = ""
        if view_set is not None:
            view_bean_list = []
            for view_id_single in view_set:
                token = self.attribute_loader.get_attribute(view_id_single)

                bean = RadiologyLoincView(
                    begin=int(token["begin"]),
                    end=int(token["end"]),
                    text=token["text"],
                    timexValue=token["text"],
                )

                view_bean_list.append(bean)
                temp_delete_view += token["text"] + "_VIEW_"

        pharmaceutical_bean_list = None
        pharmaceutical_set = crf_entity.pharmaceutical_list

        temp_delete_pharmaceutical = ""
        if pharmaceutical_bean_list is not None:
            pharmaceutical_bean_list = []
            for pharmaceutical_id_single in pharmaceutical_set:
                token = self.attribute_loader.get_attribute(pharmaceutical_id_single)

                bean = RadiologyLoincPharmaceutical(
                    begin=int(token["begin"]),
                    end=int(token["end"]),
                    text=token["text"],
                    timexValue=token["text"],
                )

                pharmaceutical_bean_list.append(bean)
                temp_delete_pharmaceutical += token["text"] + "_PHARMACEUTICAL_"

        radiologyroute_bean_list = None
        radiologyroute_set = crf_entity.radiologyroute_list
        temp_delete_radiologyroute = ""

        if radiologyroute_set is not None:
            radiologyroute_bean_list = []
            for radiologyroute_id_single in radiologyroute_set:
                token = self.attribute_loader.get_attribute(radiologyroute_id_single)

                bean = RadiologyLoincRadiologyroute(
                    begin=int(token["begin"]),
                    end=int(token["end"]),
                    text=token["text"],
                    timexValue=token["text"],
                )

                radiologyroute_bean_list.append(bean)
                temp_delete_radiologyroute += token["text"] + "_RADIOLOGYROUTE_"

        radiology_component_dto.raiology_loinc_modality_list = modality_bean_list
        radiology_component_dto.raiology_loinc_pharmaceutical_list = (
            pharmaceutical_bean_list
        )
        radiology_component_dto.raiology_loinc_radiologyroute_list = (
            radiologyroute_bean_list
        )
        radiology_component_dto.raiology_loinc_view_list = modality_bean_list

        return radiology_component_dto
