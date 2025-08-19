# LOINC SERVICE 

## Installation of the service

1. Clone the repo using the command : 
```
git clone https://git-codecommit.us-east-1.amazonaws.com/v1/repos/hnlp-loinc
```
and give your username and password.

2. Find the database at : `https://drive.google.com/drive/folders/1dTEX0bwhZXYcj4hbQ-RRlJMv73VQlTOl?usp=drive_link` and load it into MySQL.

3. Load the Database using the following commands : 
```
mysql -u root -p
CREATE DATABASE IF NOT EXISTS LOINC;
exit;
mysql -u root -p "Name of the SQL files" < "Name of Sql File Here" # Do this for all the sql dump files 
```

4. Configure the following environmental variables : 
    - **LOINC_DB_HOST** : The host name
    - **LOINC_DB_USER** : The database user name
    - **LOINC_DB_NAME** : The Database name 
    - **LOINC_DB_PASSWD** : Database password
    - **NER_ENDPOINT_URL** : The NER service to be called. Mention only the first part of the NER service. the `/predict_str` will be added later on. 
    - **LOINC_DB_NAME** : Table name inside the LOINC database. 
    - **UMLS_DB_NAME** : UMLS Table name inside UMLS database.

5. Create a virtual environment using the command (using conda): 
```
# Using conda, and the .yml file
conda create --name loinc
```

6. Activate the virtual environment using the commmand : 
```
conda activate loinc
```

7. Install required libraries : 
```
pip3 install -r requirements.txt
```

8. To start the service -
    - **On Windows** - Use loinc_script.ps1 to mention the enviromental variables. 
    - **On Linux** - Use loinc_script.sh to run after mentioning the environmental variables. 
    - **On server** - Mention the environmental variables in config map and then just do `python main.py`

9. The port is **3001** and can be changed in `config.py`. The loinc host is **0.0.0.0**.  
10. Once the service is up and running we can access it using this command : 

```python3
def get_loinc_entity_output(doc):
    #print("Calling the ner pipeline output")
    url = "http://localhost:3001/loinc_output"
    with open(doc, 'r', encoding='utf8') as fopen:
        text = fopen.read()
    data = json.dumps({"content": text})
    res = requests.post(url, headers={'Content-type': 'application/json'}, data=data)
    return res.text

out_lst = get_loinc_entity_output("file_path_goes_here")
print(out_lst)
```