import requests
import json
import pathlib
import logging
import json
import datetime

import ckan.plugins.toolkit as toolkit
from ckan.common import config
import ckan.logic as logic
import ckan.model as model
import ckan.lib.dictization.model_dictize as model_dictize
import pytz

import ckanext.bankofengland.helpers as boe_helpers
import ckanext.bankofengland.model as boe_model


log = logging.getLogger(__name__)


def build_id(input):
    return "__".join(sorted(input))


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
    resources = data_dict.get("resources", [])

    for resource in resources:
        if resource.get('publish_date_date') or resource.get('publish_date_time'):
            date = resource['publish_date_date']
            time = resource['publish_date_time']

            if date and not time:
                time = '00:00'
                resource['publish_date_time'] = time

            if time and not date:
                date = datetime.datetime.now().strftime('%Y-%m-%d')
                resource['publish_date_date'] = date

            dt = datetime.datetime.strptime(date + ' ' + time, '%Y-%m-%d %H:%M')
            resource['publish_date'] = dt.isoformat()

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
@toolkit.side_effect_free
def package_show(original_action, context, data_dict):
    result = original_action(context, data_dict)

    if context.get('creating_alias', False):
        return result

    filtered_result = filter_unpublished_resources(context, result, single=True)

    return filtered_result


@toolkit.chained_action
@toolkit.side_effect_free
def resource_show(original_action, context, data_dict):
    result = original_action(context, data_dict)

    footnotes = boe_model.get_footnotes(resource_id=result['id'])
    result['footnotes'] = footnotes
    for footnote in result['footnotes']:
        footnote['row'] = footnote['row'].isoformat()

    return result


@toolkit.chained_action
@toolkit.side_effect_free
def package_search(original_action, context, data_dict):
    result = original_action(context, data_dict)
    filtered_result = filter_unpublished_resources(context, result)

    return filtered_result


def filter_unpublished_resources(context, result, single=False):
    auth_user_obj = context.get('auth_user_obj')

    if auth_user_obj and auth_user_obj.sysadmin:
        return result

    user = context.get('user')
    filtered_result = result

    organizations_available = logic.get_action('organization_list_for_user')(
        {'user': user}, {}
    )
    org_permissions = {}

    if organizations_available:
        for org in organizations_available:
            org_permissions[org['name']] = org['capacity']

    if single:
        package_org = result.get('organization', {})
        org_name = package_org.get('name')

        if org_name in org_permissions and org_permissions[org_name] in ['admin', 'editor']:
            return filtered_result

        filtered_result = boe_helpers.filter_unpublished_resources(result)
    else:
        filtered_tmp = []

        for package in result.get('results', []):
            package_org = package.get('organization', {})
            org_name = package_org.get('name')

            if org_name not in org_permissions or org_permissions[org_name] not in ['admin', 'editor']:
                filtered_package = boe_helpers.filter_unpublished_resources(package)
            else:
                filtered_package = package

            filtered_tmp.append(filtered_package)

        filtered_result['results'] = filtered_tmp

    return filtered_result


@toolkit.side_effect_free
def resource_show_by_name(context, data_dict):
    log.error('resource_show_by_name')
    utc=pytz.UTC
    resource = model.Resource.get(data_dict['id'])
    if not resource:
        raise toolkit.ObjectNotFound
    resource = model_dictize.resource_dictize(resource, context)

    footnotes = boe_model.get_footnotes(resource_id=resource['id'])
    resource['footnotes'] = footnotes
    for footnote in resource['footnotes']:
        footnote['row'] = footnote['row'].isoformat()

    if 'publish_date' not in resource:
        return resource
    resource_date = datetime.datetime.strptime(resource['publish_date'], '%Y-%m-%dT%H:%M:%S')
    if datetime.datetime.now(datetime.timezone.utc) > utc.localize(resource_date):
        return resource
    else:
        try:
            access = toolkit.check_access('resource_update', context, data_dict)
            if access:
                return resource
        except:
            raise toolkit.NotAuthorized("This resource has not been published yet")


@toolkit.side_effect_free
def footnotes_show(context, data_dict):
    resource_id = data_dict.get('resource_id')
    resource_name = data_dict.get('resource_name')

    if resource_id:
        return boe_model.get_footnotes(resource_id=resource_id)
    elif resource_name:
        return boe_model.get_footnotes(resource_name=resource_name)
    else:
        log.error('No resource_id or resource_name provided')
        return []


@toolkit.side_effect_free
def update_footnote(context, data_dict):
    resource_id = data_dict.get('resource_id')
    row = data_dict.get('row')
    column = data_dict.get('column')
    footnote = data_dict.get('footnote')
    footnote_id = data_dict.get('footnote_id')

    if not footnote:
        log.error('Failed to update footnote. No footnote provided')
        return []

    if footnote_id:
        return boe_model.update_footnote(
            footnote_id=footnote_id, footnote=footnote
        )

    if not resource_id and column:
        resource_id = toolkit.get_action('resource_show_by_name')(
            context, {'id': column}
        )['id']

    if not all([resource_id, row, column]):
        log.error(
            'Failed to update footnote. Missing parameters.\n'
            'Must include resource_id, row, column, and footnote'
        )
        return []

    return boe_model.update_footnote(
        resource_id=resource_id, row=row, column=column, footnote=footnote
    )


@toolkit.side_effect_free
def create_footnote(context, data_dict):
    resource_id = data_dict.get('resource_id')
    row = data_dict.get('row')
    column = data_dict.get('column')
    footnote = data_dict.get('footnote')

    if not resource_id and column:
        resource_id = toolkit.get_action('resource_show_by_name')(
            context, {'id': column.lower()}
        )['id']

    if not all([resource_id, row, column, footnote]):
        log.error(
            'Failed to create footnote. Missing parameters.\n'
            'Must include resource_id, row, column, and footnote'
        )
        return []

    return boe_model.create_footnote(
        resource_id=resource_id, row=row, column=column, footnote=footnote
    )


@toolkit.side_effect_free
def delete_footnote(context, data_dict):
    footnote_id = data_dict.get('footnote_id')
    resource_id = data_dict.get('resource_id')
    row = data_dict.get('row')
    column = data_dict.get('column')

    if not resource_id and column:
        resource_id = toolkit.get_action('resource_show_by_name')(
            context, {'id': column}
        )['id']

    if not all([resource_id, row, column]):
        log.error(
            'Failed to delete footnote. Missing parameters.\n'
            'Must include resource_id, row, column, and footnote_id'
        )
        return []

    return boe_model.delete_footnote(
        footnote_id=footnote_id, resource_id=resource_id,
        row=row, column=column
    )
