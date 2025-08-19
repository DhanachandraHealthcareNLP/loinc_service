import os
from dotenv import load_dotenv

load_dotenv()

# Database Configs
HOST = os.getenv("LOINC_DB_HOST")
USER = os.getenv("LOINC_DB_USER")
DATABASE = os.getenv("LOINC_DB_NAME")
PASSWORD = os.getenv("LOINC_DB_PASSWD")

LOINC_TABLE_NAME = os.getenv("LOINC_TABLE_NAME") # This gets assigned to the variables in "core\impl\classes\my_sql.py" also.
UMLS_TABLE_NAME = os.getenv("UMLS_TABLE_NAME")

# Loinc Configuration
LOINC_HOST = "0.0.0.0"
LOINC_PORT = 3001
NER_ENDPOINT_URL = os.getenv("NER_ENDPOINT_URL")
# NER_ENDPOINT_URL = "https://hnlphcntemp.shaip.com/predict_hcc_str"
