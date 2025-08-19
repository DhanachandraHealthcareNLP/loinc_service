#!/bin/bash

# Set environmental variables
export LOINC_DB_HOST=""
export LOINC_DB_USER=""
export LOINC_DB_NAME=""
export LOINC_DB_PASSWD=""
export UMLS=""
export NER_ENDPOINT_URL=""

# Activate the Conda environment named "base"
# conda activate base

# Call the Python file "main.py"
python main.py
