import logging
from flask import Blueprint
import datetime
import json

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.model as model
import ckan.logic as logic
from ckan.common import g, request

from ckanext.bankofengland import helpers as boe_helpers

log = logging.getLogger(__name__)


boe_resource = Blueprint(
    'boe_resource', __name__,
    url_prefix='/dataset/<id>/resource/<resource_id>'
)


def _get_context():
    context = {
        'model': model,
        'session': model.Session,
        'user': g.user,
        'auth_user_obj': g.userobj
    }

    return context


def footnotes(id, resource_id):
    context = _get_context()

    pkg_dict = logic.get_action('package_show')(
        context, {'id': id}
    )
    resource = logic.get_action('resource_show')(
        context, {'id': resource_id}
    )
    req_args = request.args

    if request.method == 'POST':
        req_form = request.form
        footnotes_deleted = req_form.get('footnote-rows-deleted')

        if footnotes_deleted:
            footnotes_deleted = json.loads(footnotes_deleted)

            for footnote in footnotes_deleted:
                try:
                    logic.get_action('delete_footnote')(
                        context,
                        {
                            'resource_id': resource_id,
                            'row': datetime.datetime.strptime(
                                footnote['row'], '%Y-%m-%d %H:%M:%S'
                            ),
                            'column': footnote['column']
                        }
                    )
                except Exception as e:
                    log.error(e)

        def _check_if_key_exists(key, dictionary):
            if key not in dictionary:
                dictionary[key] = {}


        def _footnote_action(action, footnote_dict):
            for key, value in footnote_dict.items():
                footnote = {
                    'resource_id': resource_id,
                    'row': value['row'],
                    'column': value['column'],
                    'footnote': value['text']
                }

                try:
                    logic.get_action(action)(context, footnote)
                except Exception as e:
                    log.error(e)


        footnotes = {}
        new_footnotes = {}

        for key, value in req_form.items():
            is_new = False

            if key.endswith('-new'):
                key = key.replace('-new', '')
                is_new = True

            if key.startswith('footnote-row-'):
                key = key.replace('footnote-row-', '')

                if is_new:
                    _check_if_key_exists(key, new_footnotes)
                    new_footnotes[key]['row'] = value
                else:
                    _check_if_key_exists(key, footnotes)
                    footnotes[key]['row'] = value
            elif key.startswith('footnote-column-'):
                key = key.replace('footnote-column-', '')

                if is_new:
                    _check_if_key_exists(key, new_footnotes)
                    new_footnotes[key]['column'] = value
                else:
                    _check_if_key_exists(key, footnotes)
                    footnotes[key]['column'] = value
            elif key.startswith('footnote-text-'):
                key = key.replace('footnote-text-', '')

                if is_new:
                    _check_if_key_exists(key, new_footnotes)
                    new_footnotes[key]['text'] = value
                else:
                    _check_if_key_exists(key, footnotes)
                    footnotes[key]['text'] = value

        _footnote_action('create_footnote', new_footnotes)
        _footnote_action('update_footnote', footnotes)

        h.flash_success('Footnotes successfully updated')

    resource_name = req_args.get('resource_name', resource.get('name'))

    if not resource_name:
        resource_name = resource_id
    else:
        resource_name = resource_name

    row_values = boe_helpers.get_footnote_rows(resource_id)

    existing_footnotes = logic.get_action('footnotes_show')(
        context, {'resource_id': resource_id}
    )
    js_row_values = json.dumps([
        row_value.strftime('%Y-%m-%d %H:%M:%S') for row_value in row_values
    ])

    extra_vars = {
        'pkg_dict': pkg_dict,
        'resource': resource,
        'resource_name': resource_name,
        'footnotes': existing_footnotes,
        'row_values': row_values,
        'js_row_values': js_row_values
    }

    return base.render(
        'package/resource_footnotes.html',
        extra_vars=extra_vars
    )


def register_boe_plugin_rules(blueprint):
    blueprint.add_url_rule(
        '/footnotes',
        view_func=footnotes,
        methods=['GET', 'POST']
    )

register_boe_plugin_rules(boe_resource)
