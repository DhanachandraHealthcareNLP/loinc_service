# Set environmental variables
$env:LOINC_DB_HOST = "127.0.0.1"
$env:LOINC_DB_USER = "root"
$env:LOINC_DB_NAME = "LOINC"
$env:LOINC_DB_PASSWD = ""

$env:NER_ENDPOINT_URL = "http://127.0.0.1:5002"
$env:UMLS_DB_NAME = "UMLS_2014"
$env:LOINC_DB_NAME = "LOINC"

# Activate the Conda environment named "base"
# conda activate base

# Call the Python file "main.py"
python main.py
