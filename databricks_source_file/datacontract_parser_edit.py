# Databricks notebook source
!pip install pyyaml

# COMMAND ----------

import requests
import yaml
import os

# COMMAND ----------

github_file_url = dbutils.widgets.get("github_url")
sigla = dbutils.widgets.get("sigla")
os.environ['cost_center'] = sigla

# COMMAND ----------

print(f"GitHub URL: {github_file_url}")
print(f"Sigla: {sigla}")

# COMMAND ----------

github_token = dbutils.secrets.get(scope="github_token", key="github-token")

headers = {
    'Authorization': f'Bearer {github_token}',
    'Accept': 'application/vnd.github.v3.raw'
}

try:
    response = requests.get(github_file_url, headers=headers)
    response.raise_for_status()
    datacontract_dict = yaml.safe_load(response.text)
    print("Data contract loaded successfully.")
except Exception as e:
    print(f"Error loading data contract: {e}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Funções Auxiliares

# COMMAND ----------

def get_schema_table_name(contract_dict):
    table_name = contract_dict.get("name")
    
    # Tenta pegar a camada medallion por nome na lista de propriedades
    custom_props = contract_dict.get("customProperties", [])
    medallion_layer = ""
    for prop in custom_props:
        if prop.get("property") == "medallion_layer":
            val = prop.get("value")
            medallion_layer = val[0] if isinstance(val, list) else val
            break
            
    # Fallback para o índice 4 caso não tenha propriedade (legado)
    if not medallion_layer and len(custom_props) > 4:
        val = custom_props[4].get("value")
        medallion_layer = val[0] if isinstance(val, list) else val
        
    schema = f"{medallion_layer}_{sigla}"
    return f"satus.{schema}.{table_name}".lower()


def build_columns_sql(contract_dict):
    columns_schema = contract_dict.get("schema", [{}])[0].get("properties", [])
    columns_sql = ""
    primary_key = None
    partition_key = None
    
    for column in columns_schema:
        col_name = column.get('name')
        col_type = column.get('physicalType')
        col_desc = column.get('description', '')
        
        columns_sql += f"{col_name} {col_type} COMMENT '{col_desc}',\n\t"
        
        if column.get('primaryKey'):
            pk = column.get('primaryKey')
            primary_key = pk[0] if isinstance(pk, list) else pk
            
        if column.get('partitionKey'):
            part_k = column.get('partitionKey')
            partition_key = part_k[0] if isinstance(part_k, list) else part_k

    columns_sql = columns_sql.rstrip().rstrip(',')

    if primary_key:
        columns_sql += f",\n\tPRIMARY KEY ({primary_key})"
        
    partition_clause = f"PARTITIONED BY ({partition_key})" if partition_key else ""
    
    return columns_sql, partition_clause


def execute_table_sql(schema_table_name, table_description, columns_sql, partition_clause, is_edit=False):
    create_statement = "CREATE OR REPLACE TABLE" if is_edit else "CREATE TABLE IF NOT EXISTS"
    
    sql_command = f"""{create_statement} {schema_table_name} (
        {columns_sql}
    )
    USING DELTA
    {partition_clause}
    COMMENT '{table_description}'
    TBLPROPERTIES (
        'delta.autoOptimize.optimizeWrite' = 'true',
        'delta.autoOptimize.autoCompact' = 'true'
    )"""

    print(f"Command SQL:\n{sql_command}")
    return spark.sql(sql_command)


def add_table_tags(contract_dict, schema_table_name):
    team = contract_dict.get("team", {}).get("name", "")
    sla_properties = contract_dict.get("slaProperties", [])
    custom_properties = contract_dict.get("customProperties", [])
    
    tags_list = [f"'team' = '{team}'"]
    
    custom_props_dict = {prop.get("property"): prop.get("value") for prop in custom_properties if prop.get("property")}
    
    prop_mapping = {
        'ingestion_id': 'ingestion_id',
        'sistema_origem': 'sistema_origem',
        'formato_origem': 'formato_origem',
        'medallion_layer': 'medallion_layer',
        'last_operation': 'last_operation'
    }
    
    for tag_key, prop_key in prop_mapping.items():
        if prop_key in custom_props_dict:
            val = custom_props_dict[prop_key]
            if isinstance(val, list) and len(val) > 0:
                val = val[0]
            tags_list.append(f"'{tag_key}' = '{val}'")
            
    if 'ingestion_id' not in custom_props_dict and len(custom_properties) > 5:
        # Fallback para posições legadas
        tags_list.append(f"'ingestion_id' = '{custom_properties[1].get('value')}'")
        tags_list.append(f"'sistema_origem' = '{custom_properties[2].get('value')}'")
        tags_list.append(f"'formato_origem' = '{custom_properties[3].get('value')}'")
        tags_list.append(f"'medallion_layer' = '{custom_properties[4].get('value')}'")
        tags_list.append(f"'last_operation' = '{custom_properties[5].get('value')}'")
            
    tags_list.append(f"'data_contract_ref' = '{github_file_url}'")
    
    for tag in sla_properties:
        tags_list.append(f"'{tag.get('property')}' = '{tag.get('value')}'")

    tags_sql = ", ".join(tags_list)
    
    add_tags_command = f"ALTER TABLE {schema_table_name} SET TAGS ({tags_sql})"
    print(f"Tags SQL:\n{add_tags_command}")
    return spark.sql(add_tags_command)


def add_column_tags(contract_dict, schema_table_name):
    columns_schema = contract_dict.get("schema", [{}])[0].get("properties", [])
    for column in columns_schema:
        col_name = column.get("name")
        columns_tags = column.get("tags", [])
        
        for tag in columns_tags:
            if ":" in tag:
                tag_property, tag_value = tag.split(":", 1)
                if tag_value and tag_value != 'None':
                    add_tags_command = f"ALTER TABLE {schema_table_name} ALTER COLUMN {col_name} SET TAGS ('{tag_property}' = '{tag_value}')"
                    print(add_tags_command)
                    spark.sql(add_tags_command)


def process_table(contract_dict, operation):
    schema_table_name = get_schema_table_name(contract_dict)
    table_description = contract_dict.get("description", {}).get("purpose", "")
    
    columns_sql, partition_clause = build_columns_sql(contract_dict)
    
    is_edit = (operation == "edit")
    execute_table_sql(schema_table_name, table_description, columns_sql, partition_clause, is_edit)
    
    add_table_tags(contract_dict, schema_table_name)
    add_column_tags(contract_dict, schema_table_name)
    print(f"Tabela {schema_table_name} processada com sucesso. Operação: {operation}")


def delete_table(contract_dict):
    schema_table_name = get_schema_table_name(contract_dict)
    sql_command = f"DROP TABLE IF EXISTS {schema_table_name}"
    print(f"Command SQL:\n{sql_command}")
    return spark.sql(sql_command)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execução Principal

# COMMAND ----------

custom_properties = datacontract_dict.get("customProperties", [])
operation = ""

for prop in custom_properties:
    if prop.get("property") == "last_operation":
        val = prop.get("value")
        operation = str(val[0] if isinstance(val, list) else val).lower()
        break

if not operation and custom_properties:
    val = custom_properties[-1].get("value", "")
    operation = str(val[0] if isinstance(val, list) else val).lower()
    
print(f"Operação identificada: {operation}")

if operation in ["create", "edit"]:
    process_table(datacontract_dict, operation)
elif operation == "delete":
    delete_table(datacontract_dict)
else:
    print(f"Operação inválida ou ausente: '{operation}'")