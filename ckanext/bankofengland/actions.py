import requests
import ckan.plugins.toolkit as toolkit
from ckan.common import config


def build_id(input):
    return "_".join(input.sort())


def build_joins(input):
    if len(input) == 1:
        return ""
    return "".join(list(map(lambda string: f'JOIN {string} USING("Date") ', input[1:])))


def build_sql(input):
    return "CREATE VIEW {table_name} AS SELECT {first_table}.\"Date\", {list_of_tables} FROM {first_table} {joins}".format(table_name = build_id(input), first_table=input[0], list_of_tables=", ".join(f'{x}."{x.upper()}"' for x in input), joins=build_joins(input))


def add_permissions(table_name):
    url = config.get("ckanext.bankofengland.hasura_url") + "/v1/metadata"
    body = {
        "type": "pg_create_select_permission",
        "args": {
            "source": config.get("ckanext.bankofengland.hasura_db"),
            "table": table_name,
            "role": "anon",
            "permission": {"columns": "*", "filter": {}, "allow_aggregations": True},
        },
    }
    headers = {
        "X-Hasura-Role": "admin",
        "X-Hasura-Admin-Secret": config.get("ckanext.bankofengland.hasura_admin_key"),
    }
    response = requests.post(url, json=body, headers=headers)
    return response.status_code


def track_view(table_name):
    url = config.get("ckanext.bankofengland.hasura_url") + "/v1/metadata"
    body = {
        "type": "pg_track_table",
        "args": {
            "source": config.get("ckanext.bankofengland.hasura_db"),
            "table": table_name,
        },
    }
    headers = {
        "X-Hasura-Role": "admin",
        "X-Hasura-Admin-Secret": config.get("ckanext.bankofengland.hasura_admin_key"),
    }
    response = requests.post(url, json=body, headers=headers)
    return response.status_code


def run_sql(query):
    url = config.get("ckanext.bankofengland.hasura_url") + "/v2/query"
    body = {
        "type": "run_sql",
        "args": {"source": config.get("ckanext.bankofengland.hasura_db"), "sql": query},
    }
    headers = {
        "X-Hasura-Role": "admin",
        "X-Hasura-Admin-Secret": config.get("ckanext.bankofengland.hasura_admin_key"),
    }
    response = requests.post(url, json=body, headers=headers)
    return response.status_code


def create_view(context, data_dict):
    if "tables" not in data_dict:
        raise toolkit.ValidationError("Missing tables value in input")
    if len(data_dict["tables"]) == 0:
        raise toolkit.ValidationError("Need to have at least one table")
    for table in data_dict["tables"]:
        if len(table) != 7:
            raise toolkit.ValidationError("Invalid table name")
    run_sql(build_sql(data_dict["tables"]))
    track_view(build_id(data_dict["tables"]))
    return add_permissions(build_id(data_dict["tables"]))
