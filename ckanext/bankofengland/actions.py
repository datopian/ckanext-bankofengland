import requests
import ckan.plugins.toolkit as toolkit
from ckan.common import config


def build_id(input):
    return "_".join(sorted(input))


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

def get_related_tags(tag):
    thesauros = toolkit.get_action('package_show')(None, { 'id': 'thesauros' })
    thesauros_base_terms_resource = list(filter(lambda x: x['name'] == 'base_term_thesauros', thesauros['resources']))[0]
    thesauros_alias_terms_resource = list(filter(lambda x: x['name'] == 'alias_terms_thesauros', thesauros['resources']))[0]
    base_term_id = toolkit.get_action('datastore_search')(None, { 'resource_id': thesauros_base_terms_resource['id'], 'filters' : { 'BASE_TERM_UNSTEMMED': tag}, 'limit': 1000 })
    if len(base_term_id['records']) == 0:
        return [tag]
    else:
        alias_terms = toolkit.get_action('datastore_search')(None, { 'resource_id': thesauros_alias_terms_resource['id'], 'filters' : { 'BASE_TERM_ID': base_term_id['records'][0]['BASE_TERM_ID']}, 'limit': 1000 })
        return [term['ALIAS_TERM_UNSTEMMED'] for term in list(alias_terms['records'])]

def flatten(l):
    return [item for sublist in l for item in sublist]

@toolkit.chained_action
def package_create(original_action, context, data_dict):
    tags = data_dict['tags'] if 'tags' in data_dict else []
    tags = [tag['name'] for tag in tags ]
    new_tags = [{'name': tag_name, 'state': 'active' } for tag_name in flatten([get_related_tags(tag) for tag in tags])]
    data_dict['tags'] = new_tags
    result = original_action(context, data_dict)
    return result

@toolkit.chained_action
def package_update(original_action, context, data_dict):
    tags = data_dict['tags'] if 'tags' in data_dict else []
    tags = [tag['name'] for tag in tags ]
    new_tags = [{'name': tag_name, 'state': 'active' } for tag_name in flatten([get_related_tags(tag) for tag in tags])]
    data_dict['tags'] = new_tags
    result = original_action(context, data_dict)
    return result
