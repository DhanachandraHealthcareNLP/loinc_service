# from dataclasses import dataclass
# from core.impl.radiology_loinc_code_algorithm import RadiologyLoincCodeAlgorithm
# from core.impl.classes.radiology_classes import *

# rad = RadiologyLoincCodeAlgorithm()

# # lst = [40405, 517667]
# # cui_map_id_list = rad.get_map_id_from_radiology_cui_mapping(lst)

# # print(cui_map_id_list)

# raiology_loinc_modality_list = [
#     RadiologyLoincModality(text="now", begin=90, end=100, timexValue="WO contrast"),
#     RadiologyLoincModality(text="first", begin=20, end=200, timexValue="1124"),
#     RadiologyLoincModality(text="second", begin=30, end=40, timexValue="14252342"),
#     RadiologyLoincModality(text="third", begin=50, end=60, timexValue="1231"),
# ]

# raiology_loinc_pharmaceutical_list = [
#     RadiologyLoincPharmaceutical(text="now", begin=1000, end=100, timexValue="746"),
#     RadiologyLoincPharmaceutical(
#         text="first", begin=1110, end=200, timexValue="123123"
#     ),
#     RadiologyLoincPharmaceutical(
#         text="second", begin=12310, end=40, timexValue="65363"
#     ),
#     RadiologyLoincPharmaceutical(text="third", begin=3210, end=60, timexValue="143"),
# ]

# raiology_loinc_radiologyroute_list = [
#     RadiologyLoincRadiologyroute(text="now", begin=34130, end=100, timexValue="7463"),
#     RadiologyLoincRadiologyroute(
#         text="first", begin=314240, end=200, timexValue="afswgsdfs"
#     ),
#     RadiologyLoincRadiologyroute(
#         text="second", begin=3544350, end=40, timexValue="pjsdgoisjg"
#     ),
#     RadiologyLoincRadiologyroute(
#         text="third", begin=2223420, end=60, timexValue="a43234234fsd"
#     ),
# ]

# raiology_loinc_view_list = [
#     RadiologyLoincView(text="now", begin=90, end=100, timexValue="afs43qfm"),
#     RadiologyLoincView(text="first", begin=20, end=200, timexValue="afs94j3rqoa"),
#     RadiologyLoincView(text="second", begin=30, end=40, timexValue="9jt4inoegavd"),
#     RadiologyLoincView(text="third", begin=50, end=60, timexValue="afs1qwas"),
# ]


# component_dto = RadiologyComponentDto(
#     raiology_loinc_modality_list=raiology_loinc_modality_list,
#     raiology_loinc_pharmaceutical_list=raiology_loinc_pharmaceutical_list,
#     raiology_loinc_radiologyroute_list=raiology_loinc_radiologyroute_list,
#     raiology_loinc_view_list=raiology_loinc_view_list,
# )

# all_components = rad.get_all_components(component_dto=component_dto)

# cui_list = ["89700-9-id", "37447-0-id", "36449-7-id", "89834-6-id"]
# res = rad.get_all_term_mapping_from_cui_mapping(cui_list)
# table_dto = res[0]

# matchcount = rad.get_total_number_of_matched_term(
#     table_dto=table_dto, all_components=all_components
# )

# evidence_lst = rad.get_text_span(
#     evidence_list=set(
#         [
#             TextSpan(
#                 "now",
#                 90,
#             ),
#             TextSpan("first", 20),
#         ]
#     ),
#     dto=table_dto,
#     all_components=all_components,
#     method_entity_mention=EntityMentionDto(begin_set=[]),
#     system_entity_mention=EntityMentionDto(begin_set=[]),
# )


import mysql.connector as Cn
from loinc_service_implementation import LoincServiceImplementation
import json
import os
from tqdm import tqdm
from pprint import pprint

# Creating a connection
connection = Cn.connect(
    host="127.0.0.1",
    user="root",
    database="LOINC",
    passwd="Tri2310s@nu",
)
service = LoincServiceImplementation(connection=connection)
# base_path = (
#     "D:/Work_Files/LOINC/server_upload_ner/download/fetch_files/output_ner_outputs/"
# )

base_path = "D:/Work_Files/LOINC/server_upload_ner/output_ner_1_corrected/output_ner_1/"
out_path = "D:/Work_Files/LOINC/testing_files/output_py_loinc_ner_1_server/"
all_files = os.listdir(base_path)

content = json.load(
    open(
        "D:/Work_Files/LOINC/server_upload_ner/output_ner_1_corrected/output_ner_1/35818_1769865_part2.json"
    )
)

res = service.invoke_core_service(document_text="", f_json=content["result"])
pprint(res)
# connection.close()

# for f in tqdm(all_files):
#     content = json.load(open(base_path + f))
#     res = service.invoke_core_service(document_text="", f_json=content["result"])
#     print(res)
#     with open(out_path + f, "w") as f:
#         json.dump(res, f)


connection.close()
