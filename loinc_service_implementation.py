import logging
import os
from typing import Dict

from core.impl.classes.core_dto import *
from core.impl.classes.loinc_classes import *
from core.impl.classes.my_sql import *
from core.impl.classes.radiology_classes import *
from core.impl.core_service_impl import CoreServiceImplementation
from core.impl.laboratory_loinc_code_service import LaboratoryLoincCodeService
from core.impl.radiology_loinc_code_service import RadiologyLoincCodeService

logging.basicConfig(
    filename="loinc_log" + os.sep + "loinc.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filemode="a",
)


class LoincServiceImplementation:
    def __init__(self, connection) -> None:
        self.cDoc = None
        self.connection = connection
        self.core_service_impl = CoreServiceImplementation()

    def invoke_core_service(self, document_text, f_json) -> Dict:
        """
        Main entry point of the LOINC service.

        :param document_text: Document text to be proccessed (Not used, will remove later). 
        :param f_json: Json of the NER output.
        :returns: LOINC Codes in JSon format.
        """

        cDoc = f_json  # ["result"]
        loinc_final_output = None

        self.attribute_loader = AttributeLoader(cDoc=cDoc)
        self.radiology_loinc_code_service = RadiologyLoincCodeService(
            connection=self.connection, attribute_loader=self.attribute_loader
        )
        self.laboratory_loinc_code_service = LaboratoryLoincCodeService(
            connection=self.connection
        )
        self.query_my_sql = QueryMySQL(connection=self.connection)
        self.laboratory_loinc_code_service.init_loinc_service(
            connection=self.connection
        )
        self.radiology_loinc_code_service.init_radiology_loinc_service()

        start = time.time()
        loinc_final_output = self.get_loinc_codes(cDoc, "", document_text)
        end = time.time()
        final_output = {}
        final_output["timeTaken"] = str(end - start) + " secs"
        final_output["result"] = loinc_final_output

        return final_output

    def get_loinc_codes(self, cDoc, work_type_id, doc_text):
        """
        Gets the LOINC Codes.

        :param CDoc: NER Json.
        :returns: Responses from Laboratory and Radiology methods
        """
        # self.status_boundary_span_to_dict_status = (
        #     self.core_service_impl.get_status_data(cDoc)
        # )
        # self.negation_boundary_span_to_polarity_status = (
        #     self.core_service_impl.get_negation_data(cDoc)
        # )
        # self.sec_beg_end_to_name = self.core_service_impl.get_section_data(cDoc)
        self.sent_to_entity_map = self.core_service_impl.get_entity_mention_data(cDoc)
        self.crf_beg_end_to_crf_mention: Dict[
            Span, CRFEntityMention
        ] = self.core_service_impl.get_crf_entity_data(cDoc)

        self.get_laboratory_loic_codes(cDoc)
        self.get_radiology_loinc_code()

        responses = self.get_required_output_format()
        return responses

    def get_laboratory_loic_codes(self, cDoc):
        """
        Gets the Laboratory Loinc Codes.

        :param cDoc: NER Json.
        :returns: None.
        """
        self.loinc_code_set: Set[LoincCodeBean] = set()

        for entity in cDoc["entities"]:
            beg_array = [ent["begin"] for ent in entity["textSpan"]]
            end_array = [ent["end"] for ent in entity["textSpan"]]
            entity_array = [ent["text"] for ent in entity["textSpan"]]

            text_span_list = []
            i = 0
            for s in beg_array:
                beg = int(s)
                span = TextSpan(text=entity_array[i], begin_offset=beg)
                i += 1
                text_span_list.append(span)

            ner_umls_data = self.get_Umls_Data(entity)

            entity_type = entity["type"]
            if entity_type == "LABORATORY_DATA":
                logging.info(f"==> Entity with the 'LABORATORY DATA FOUND': {entity}")
                loinc_code = self.generate_loinc_codes(entity, ner_umls_data)

                if loinc_code is not None and loinc_code.code != "":
                    self.loinc_code_set.add(loinc_code)

    def get_Umls_Data(self, data):
        """
        Gets the UMLS Data from the NER segment of the entity. 

        :param data: JSON doct of the entity.
        :returns: UMLS data. 
        """

        umls_data = data["metadata"]["normalization"]
        return umls_data

    def generate_loinc_codes(self, entity, ner_umls_data):
        """
        Gets the LOINC Code using Laboratory Method ater extracting required components. 

        :param entity: Entity dict.
        :param ner_umls_data: The NER UMLS Data.
        :returns: Loinc Code for the entity if present. 
        """

        component = " ".join(ent["text"] for ent in entity["textSpan"])
        method_id_set = [it for it in entity["metadata"]["labData"]["method"]]
        system_id_set = [it for it in entity["metadata"]["labData"]["system"]]
        unit_id_set = [it for it in entity["metadata"]["labData"]["unit"]]

        method_list = None
        system_list = None
        unit_list = None
        component_list = None

        modified_component = self.get_modified_component_for_accuracy_improvement(
            component
        )

        component_bean = LoincComponent(
            text=component,
            timex_value=modified_component,
            begin=entity["textSpan"][0]["begin"],
            end=entity["textSpan"][0]["end"],
        )

        temp_delete_cuis = ""
        cuit_set = set()
        for it in ner_umls_data:
            for cui in it["cuis"]:
                # As Cui's are of the form : C0011847, we take only the numerical part.
                filtered_cui = cui.split("C")[-1]
                cuit_set.add(int(filtered_cui))
                temp_delete_cuis += filtered_cui + "_CUI_"

        cuit_set = list(cuit_set)
        component_bean.cui_set = cuit_set

        temp_delete_unit = ""
        if unit_id_set is not None:
            unit_bean = LoincUnit()
            for unit_id_single in unit_id_set:
                token = self.attribute_loader.get_attribute(unit_id_single)
                if token is not None : 
                    temp_delete_unit += token["text"]
                    unit_bean.begin = int(token["begin"])
                    unit_bean.end = int(token["end"])
                    unit_bean.timexValue = token["text"]
                    unit_bean.text = token["text"]
                    break

        temp_delete_method = ""
        if method_id_set is not None:
            method_bean_list = []
            for method_id_single in method_id_set:
                token = self.attribute_loader.get_attribute(method_id_single)
                if token is not None : 
                    bean = LoincMethod(
                        begin=int(token["begin"]),
                        end=int(token["end"]),
                        text=token["text"],
                        timexValue=token["text"],  # TODO: Change the text to timexValue
                    )
                    method_bean_list.append(bean)
                    temp_delete_method += token["text"] + "_METHOD_"

        temp_delete_system = ""
        if system_id_set is not None:
            system_bean_list = []
            for system_id_single in system_id_set:
                token = self.attribute_loader.get_attribute(system_id_single)
                if token is not None : 
                    bean = LoincSystem(
                        begin=int(token["begin"]),
                        end=int(token["end"]),
                        text=token["text"],
                        timexValue=token["text"],  # TODO: Change the text to timexValue
                    )
                    system_bean_list.append(bean)
                    temp_delete_system += token["text"] + "_SYSTEM_"

        logging.info(f"==> From the entity, component_bean: {component_bean}, unit_bean: {unit_bean}, system_beans_list: {system_bean_list}, method_beans: {method_bean_list}")

        loinc_codebean = self.laboratory_loinc_code_service.start_suggesting_code(
            component_bean=component_bean,
            unit_bean=unit_bean,
            system_beans=system_bean_list,
            scale=None,
            time=None,
            method_beans=method_bean_list,
        )

        return loinc_codebean

    def get_modified_component_for_accuracy_improvement(self, component: str):
        """
        Modifies the component for accuracy improvement. 

        :param component: Text of the component.
        :returns: Modified component. 
        """

        if component.strip().lower() in [
            "blood glucose",
            "glucose blood",
            "bld glucose",
            "glucose bld",
            "urine glucose",
            "ur glucose",
            "glucose urine",
            "glucose ur",
            "glucose level"  # Added to accomodate Glucose Level in the DB.
        ]:
            return "Glucose"

        if component.strip().lower() in [
            "cr",
            "creat",
            "blood cr",
            "cr blood",
            "urine cr",
            "cr urine",
        ]:
            return "Creatinine"

        if component.strip().lower() in [
            "blood creatinine",
            "creatinine blood",
            "bld creatinine",
            "creatinine bld",
            "urine creatinine",
            "ur creatinine",
            "creatinine urine",
            "creatinine ur",
        ]:
            return "Creatinine"

        if component.strip().lower() in [
            "serum alcohol",
            "alcohol serum",
            "alcohol ser",
            "ser alcohol",
            "serum alcohol level",
        ]:
            return "Alcohol"

        if component.strip().lower() in [
            "serum sodium",
            "sodium serum",
            "sodium ser",
            "ser sodium",
        ]:
            return "Sodium"

        return component

    def get_radiology_loinc_code(self):
        """
        Get the LOINC codes using the Radiology method. 

        
        :returns: None, just appends the found code beans to the list of all loinc code beans. 
        """

        logging.info("==> Inside Radiology Loinc Code !")

        radiology_loinc_code_set: Set[RadiologyLoincCodeBean] = set()

        for sent, entity_mention_dto in self.sent_to_entity_map.items():

            logging.info(f"==> Looking at sentence : {sent} and the entities : {entity_mention_dto}")
            
            if sent.sentence_num == 16: 
                a=1
            radiology_loinc_code_set = (
                self.radiology_loinc_code_service.find_radiology_loinc_code(
                    sent=sent,
                    entity_mention_dto_set=entity_mention_dto,
                    crf_beg_end_to_crf_mention=self.crf_beg_end_to_crf_mention,
                    radiology_loinc_code_bean_set=radiology_loinc_code_set,
                )
            )

        for radiology_code_bean in radiology_loinc_code_set:
            loinc_code_bean = self.query_my_sql.get_loinc_master_data_from_code(
                code=radiology_code_bean.code, text_span=radiology_code_bean.text_spans
            )

            if loinc_code_bean is not None:
                self.loinc_code_set.add(loinc_code_bean)

    def get_required_output_format(self):
        """
        Returns the output of the loinc codes in required format 

        :returns: Json dict of the output LOINC codes that are found. 
        """

        responses = []
        id = 0
        for loinc_code_bean in self.loinc_code_set:
            resp = {}
            resp["id"] = id
            resp["code"] = loinc_code_bean.code
            resp["codeDescription"] = loinc_code_bean.code_desciption
            resp["codingSystem"] = "LOINC"

            text = ""
            textSpans = []
            for span in loinc_code_bean.textSpans:
                new_span = {"text": span.text, "beginOffset": span.begin_offset}
                textSpans.append(new_span)

                text += span.text + " "

            resp["text"] = text
            resp["textSpans"] = textSpans

            responses.append(resp)
            id += 1

        return responses

