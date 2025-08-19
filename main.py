import copy
import json
import logging
import os
from datetime import date, datetime

import mysql.connector as Cn
import pandas as pd
import requests
from flask import Flask, jsonify, request
from tqdm import tqdm
from waitress import serve

from config import *
from loinc_service_implementation import LoincServiceImplementation

app = Flask(__name__)

if not os.path.exists("loinc_log"):
    os.mkdir("loinc_log")

print(f"Log files can be found at : 'loinc_log/loinc.log'")

#Initializing the logging modules
logging.basicConfig(
    filename="loinc_log" + os.sep + "loinc.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filemode="a",
)

# Creating a connection
connection = Cn.connect(
    host=HOST,
    user=USER,
    database=DATABASE,
    passwd=PASSWORD,
)


def get_ner_ent_content(text_dict, ner_version):
    """
    Gets the relevant entities from the Json entities as well as the relationships.

    :param text_dict: JSON output from the NER-2.0 API.
    :returns: List of all the entities in correct format as required by the SNOMED code.
    :returns: List of tokens.
    """

    if ner_version == 1:
        return text_dict

    map = pd.read_csv("resources/Guideline_Mapping.csv")
    map["New_entity_type"] = map["New_entity_type"].apply(lambda x: str(x).upper())
    map["Old_entity_type_1"] = map["Old_entity_type_1"].apply(lambda x: str(x).upper())
    map["Old_entity_type_2"] = map["Old_entity_type_2"].apply(lambda x: str(x).upper())

    mp = {}
    for row in map.itertuples(index=False):
        mp[row[0]] = [row[1], row[2]]

    new_text_dict = copy.deepcopy(text_dict)
    text_dict = text_dict["result"]
    all_entities = text_dict["entities"]
    contextTokens = text_dict["contextTokens"]

    tokens = []
    for token in contextTokens:
        tokens.append([token["text"], int(token["begin"]), int(token["end"])])

    tokens.sort(key=lambda x: x[1])

    ret_ent = []

    for ent in all_entities:
        newtype = mp[ent["type"].upper()]

        if newtype[0] != "NAN":
            n_type = newtype[0]
            ent_copy = copy.deepcopy(ent)
            ent_copy["type"] = n_type

            ret_ent.append(ent_copy)

        if newtype[1] != "NAN":
            n_type = newtype[1]
            ent_copy = copy.deepcopy(ent)
            ent_copy["type"] = n_type

            ret_ent.append(ent_copy)

    new_text_dict["result"]["entities"] = ret_ent

    return new_text_dict


def get_ner_output(text):
    """
    Gets the NER-2.0 output.

    :param text: Document to be proccessed.
    :returns: Json output from the NER-2.0 API
    """
    url = NER_ENDPOINT_URL + "/predict_ner_str"
    logging.info(f"==> Serving NER url at : {url}")
    
    data = {"content": text, "servicingFacility": "RUMC"}
    res = requests.post(url, headers={"Content-type": "application/json"}, json=data)
    output = res.text
    return json.loads(output)


def get_labdata_values(text_dict):
    new_entites = []
    old_entities = text_dict["result"]["entities"]
    relations = text_dict["result"]["relations"]

    for ent in old_entities:
        unit_list = []
        method_list = []
        value_list = []
        system_list = []

        ent_id = ent["id"]

        for rel in relations:
            if rel["head"]["id"] == ent_id:
                tail_type = rel["tail"]["type"]
                ttype = tail_type.split("_")[0]
                if ttype == "VALUE":
                    value_list.append(rel["tail"]["id"])
                if ttype == "METHOD":
                    method_list.append(rel["tail"]["id"])
                if ttype == "SYSTEM":
                    system_list.append(rel["tail"]["id"])
                if ttype == "UNIT":
                    unit_list.append(rel["tail"]["id"])

        new_ent = copy.deepcopy(ent)
        new_ent["metadata"]["labData"]["unit"] = unit_list
        new_ent["metadata"]["labData"]["value"] = value_list
        new_ent["metadata"]["labData"]["system"] = system_list
        new_ent["metadata"]["labData"]["method"] = method_list

        new_entites.append(new_ent)

    text_dict["result"]["entities"] = new_entites

    return text_dict


@app.route("/", methods=["GET"])
def index_route():
    return jsonify({"message": "Index Route"})


@app.route("/health", methods=["GET"])
def health():
    return "200"


@app.route("/loinc_output", methods=["POST"])
def success(return_json=True):
    """
    Entry point of the API. The subsequent NER and LOINC processing are done from here.

    :returns: JSON result containing LOINC code of entities.
    """

    today = date.today()
    time = datetime.now()
    logging.info(f"==> Request recieved at : Data: {today}, Time: {time}")

    if request.method == "POST":
        service = LoincServiceImplementation(connection=connection)
        text = request.json["content"]

        print("Running NER pipeline ....")
        text_dict = get_ner_output(text)
        new_text_dict = get_ner_ent_content(text_dict=text_dict, ner_version=2)
        new_text_dict = get_labdata_values(text_dict=new_text_dict)

        # logging.info(f"==> Final NER content : {new_text_dict}")

        print("Running LOINC code ......")
        logging.info(f"==> Starting LOINC service ...")

        res_dict = service.invoke_core_service(
            document_text="", f_json=new_text_dict["result"]
        )

        final_dict = {}
        final_dict["status"] = "COMPLETED"
        final_dict["codes"] = res_dict

        print("Finished !")
        logging.info(f"==> -------------- Finished running LOINC service ------------")

        return jsonify(final_dict)

    return jsonify({"msg": "Error"})


if __name__ == "__main__":
    print(f"LOINC service serving on host : {LOINC_HOST} port : {LOINC_PORT}")
    today = date.today()
    time = datetime.now()
    logging.info(f"==> Starting loinc service at : {time}")
    # app.run(host=LOINC_HOST, port=LOINC_PORT, debug=True)
    serve(app=app, host=LOINC_HOST, port=LOINC_PORT)
