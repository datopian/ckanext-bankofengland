import requests
import ckan.plugins.toolkit as toolkit
from ckan.common import config
import ckan.model as model
import ckan.logic as logic
import ckan.lib.dictization.model_dictize as model_dictize
from datetime import datetime, timezone
from typing import cast
import json
import pytz
import pathlib

_check_access = logic.check_access
def build_id(input):
    return "_".join(sorted(input))


def build_joins(input):
    if len(input) == 1:
        return ""
    return "".join(list(map(lambda string: f'JOIN {string} USING("Date") ', input[1:])))


def build_sql(tables):
    return 'CREATE VIEW {table_name} AS SELECT {first_table}."Date", {list_of_tables} FROM {first_table} {joins}'.format(
        table_name=build_id([table['tableName'] for table in tables]),
        first_table=tables[0]['tableName'],
        list_of_tables=", ".join(f'{table["tableName"]}."{table["columnName"].upper()}"' for table in tables),
        joins=build_joins([table['tableName'] for table in tables]),
    )


def build_sql_history(table_name, list_of_resources):
    return 'CREATE VIEW {table_name} AS SELECT {first_table}."Date", {list_of_tables} FROM {first_table} {joins}'.format(
        table_name=table_name + "_history",
        first_table=list_of_resources[0],
        list_of_tables=", ".join(
            f'{x}."{table_name.upper()}" as {x}' for x in list_of_resources
        ),
        joins=build_joins(list_of_resources),
    )


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
    print(body, flush=True)
    headers = {
        "X-Hasura-Role": "admin",
        "X-Hasura-Admin-Secret": config.get("ckanext.bankofengland.hasura_admin_key"),
    }
    response = requests.post(url, json=body, headers=headers)
    return response.json()


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
    return response.json()


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
    return response.json()


def create_view(context, data_dict):
    if "tables" not in data_dict:
        raise toolkit.ValidationError("Missing tables value in input")
    if len(data_dict["tables"]) == 0:
        raise toolkit.ValidationError("Need to have at least one table")
    sql_result = run_sql(build_sql(data_dict["tables"]))
    track_view_result = track_view(build_id([table['tableName'] for table in data_dict['tables']]))
    add_permissions_result = add_permissions(build_id([table['tableName'] for table in data_dict['tables']]))
    return { "sql_result": sql_result, "track_view_result": track_view_result, "add_permissions_result": add_permissions_result }

@toolkit.side_effect_free
def get_history(context, data_dict):
    package = toolkit.get_action("package_show")(
        None, {"id": data_dict["package_id"].lower()}
    )
    resources_sorted = sorted(
        package["resources"], key=lambda d: d["created"], reverse=True
    )
    run_sql(build_sql_history(
        package["name"].lower(),
        [resource["name"].lower() for resource in resources_sorted],
    ))
    track_view(package['name'].lower() + '_history')
    add_permissions(package['name'].lower() + '_history')
    return package['name'].lower() + '_history'

@toolkit.side_effect_free
def search_package_list(context, data_dict):
    packages = toolkit.get_action('package_search')(None, { 'q': data_dict['q']})
    return [package['name'] for package in packages['results']]

def get_related_tags(tag, base_terms, alias_terms):
    base_term = list(
        filter(
            lambda term: term["BASE_TERM_UNSTEMMED"].lower() == tag.lower(), base_terms
        )
    )
    if len(base_term) == 0:
        return [tag]
    else:
        alias_terms = filter(
            lambda term: term["BASE_TERM_ID"] == base_term[0]["BASE_TERM_ID"]
            and term["INCLUDE_TERM"] != "N ",
            alias_terms,
        )
        return [term["ALIAS_TERM_UNSTEMMED"] for term in alias_terms]


def flatten(l):
    return [item for sublist in l for item in sublist]


@toolkit.chained_action
def package_create(original_action, context, data_dict):
    base_terms = json.load(
        open(str(pathlib.Path(__file__).parent.resolve()) + "/base_term_thesauros.json")
    )
    alias_terms = json.load(
        open(
            str(pathlib.Path(__file__).parent.resolve()) + "/alias_term_thesauros.json"
        )
    )
    tags = data_dict["tags"] if "tags" in data_dict else []
    tags = [tag["name"] for tag in tags]
    new_tags = [
        {"name": tag_name, "state": "active"}
        for tag_name in flatten(
            [get_related_tags(tag, base_terms, alias_terms) for tag in tags]
        )
    ]
    data_dict["tags"] = new_tags
    result = original_action(context, data_dict)
    return result


@toolkit.chained_action
def package_update(original_action, context, data_dict):
    base_terms = json.load(
        open(str(pathlib.Path(__file__).parent.resolve()) + "/base_term_thesauros.json")
    )
    alias_terms = json.load(
        open(
            str(pathlib.Path(__file__).parent.resolve()) + "/alias_term_thesauros.json"
        )
    )
    tags = data_dict["tags"] if "tags" in data_dict else []
    tags = [tag["name"] for tag in tags]
    new_tags = [
        {"name": tag_name, "state": "active"}
        for tag_name in flatten(
            [get_related_tags(tag, base_terms, alias_terms) for tag in tags]
        )
    ]
    data_dict["tags"] = new_tags
    result = original_action(context, data_dict)
    return result

@toolkit.side_effect_free
def resource_show(context, data_dict):
    utc=pytz.UTC
    resource = model.Resource.get(data_dict['id'])
    if not resource:
        raise toolkit.ObjectNotFound
    resource = model_dictize.resource_dictize(resource, context)
    resource_date = datetime.strptime(resource['publish_date'], '%Y-%m-%dT%H:%M:%S')
    if datetime.now(timezone.utc) > utc.localize(resource_date):
        return resource
    else:
        try:
            access = toolkit.check_access('resource_update', context, data_dict)
            if access:
                return resource
        except:
            raise toolkit.NotAuthorized("This resource has not been published yet")
