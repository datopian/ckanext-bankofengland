import requests
import json
import pathlib
import logging
import hashlib
import difflib
from sqlalchemy import MetaData
import random
import string

import ckan.plugins.toolkit as toolkit
from ckan.common import config, c
import ckan.model as model


log = logging.getLogger(__name__)


def _get_context():
    user = c.user
    context = {
        "model": model,
        "session": model.Session,
        "user": user,
        "auth_user_obj": c.userobj,
    }
    return context

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

@toolkit.side_effect_free
def search_package_list(context, data_dict):
    packages = toolkit.get_action('package_search')(None, { 'q': data_dict['q']})
    return [package['name'] for package in packages['results']]

def get_related_tags(tag, base_terms, alias_terms):
    base_term = list(filter(lambda term: term['BASE_TERM_UNSTEMMED'].lower() == tag.lower(), base_terms))
    if len(base_term) == 0:
        return [tag]
    else:
        alias_terms = filter(lambda term: term['BASE_TERM_ID'] == base_term[0]['BASE_TERM_ID'] and term['INCLUDE_TERM'] != 'N ', alias_terms)
        return [term['ALIAS_TERM_UNSTEMMED'] for term in alias_terms]

def flatten(l):
    return [item for sublist in l for item in sublist]

@toolkit.chained_action
def package_create(original_action, context, data_dict):
    base_terms = json.load(open(str(pathlib.Path(__file__).parent.resolve()) + '/base_term_thesauros.json'))
    alias_terms = json.load(open(str(pathlib.Path(__file__).parent.resolve()) + '/alias_term_thesauros.json'))
    tags = data_dict['tags'] if 'tags' in data_dict else []
    tags = [tag['name'] for tag in tags ]
    new_tags = [{'name': tag_name, 'state': 'active' } for tag_name in flatten([get_related_tags(tag, base_terms, alias_terms) for tag in tags])]
    data_dict['tags'] = new_tags
    result = original_action(context, data_dict)
    return result

@toolkit.chained_action
def package_update(original_action, context, data_dict):
    resources = data_dict.get('resources')

    if resources:
        resource_version_errors = create_resource_versions(
            context,
            resources
        )

    base_terms = json.load(open(str(pathlib.Path(__file__).parent.resolve()) + '/base_term_thesauros.json'))
    alias_terms = json.load(open(str(pathlib.Path(__file__).parent.resolve()) + '/alias_term_thesauros.json'))
    tags = data_dict['tags'] if 'tags' in data_dict else []
    tags = [tag['name'] for tag in tags ]
    new_tags = [{'name': tag_name, 'state': 'active' } for tag_name in flatten([get_related_tags(tag, base_terms, alias_terms) for tag in tags])]
    data_dict['tags'] = new_tags
    result = original_action(context, data_dict)
    return result

@toolkit.chained_action
def resource_create(original_action, context, data_dict):
    result = original_action(context, data_dict)
    create_resource_versions(context, [result])

    return result

@toolkit.chained_action
def resource_update(original_action, context, data_dict):
    result = original_action(context, data_dict)
    create_resource_versions(context, [result])

    return result

def create_resource_versions(context, resources):
    errors = []

    for resource in resources:
        resource_id = resource.get('id')

        if resource_id:
            resource_error = {resource_id: []}

            log.info(
                'Creating new version for resource: {}'
                .format(resource_id)
            )

            try:
                versions_table = get_table('version')
                resource_hash = resource.get('hash')

                version_exists = model.Session.query(versions_table).filter(
                    versions_table.c.resource_id == resource_id,
                    versions_table.c.sha256 == resource_hash
                ).first()

                version_name = ''.join(
                    random.choice(string.ascii_letters + string.digits)
                    for _ in range(30)
                )

                if not version_exists:
                    version = toolkit.get_action('resource_version_create')(
                        context, {
                            'resource_id': resource_id,
                            'name': version_name,
                            'notes': resource.get('description'),
                            'sha256': resource.get('hash'),
                            'size': resource.get('size'),
                        }
                    )
                    log.info('New version created: {}'.format(version))
                else:
                    log.info(
                        'Versions are already up-to-date for resource: {}'
                        .format(resource_id)
                    )
            except Exception as e:
                log.error(
                    'Error creating new version for resource: {}'
                    .format(e)
                )
                resource_error[resource_id].append(e)

            errors.append(resource_error)

    return errors

def get_table(name):
    meta = MetaData()
    meta.reflect(bind=model.meta.engine)
    table = meta.tables[name]

    return table

def get_resource_from_blob(resource_dict):
    context = _get_context()

    version = toolkit.get_action('get_resource_download_spec')(
        context,
        data_dict=resource_dict
    )

    req = requests.get(version['href'])

    return [line for line in req.text.split('\n') if line != '']

@toolkit.side_effect_free
def get_resource_version_diffs(context, data_dict):
    version_a_id = data_dict.get('version_a')
    version_b_id = data_dict.get('version_b')
    version_a_dict = toolkit.get_action('version_show')(
        context,
        data_dict={'version_id': version_a_id}
    )
    version_b_dict = toolkit.get_action('version_show')(
        context,
        data_dict={'version_id': version_b_id}
    )

    version_a = get_resource_from_blob({
        'id': version_a_dict.get('resource_id'),
        'lfs_prefix': 'ckan/{}'.format(version_a_dict.get('package_id')),
        'sha256': version_a_dict.get('sha256'),
        'size': int(version_a_dict.get('size'))
    })

    version_b = get_resource_from_blob({
        'id': version_b_dict.get('resource_id'),
        'lfs_prefix': 'ckan/{}'.format(version_b_dict.get('package_id')),
        'sha256': version_b_dict.get('sha256'),
        'size': int(version_b_dict.get('size'))
    })

    version_diff = difflib.HtmlDiff().make_file(
        version_a,
        version_b,
        context=True,
    )

    return version_diff
