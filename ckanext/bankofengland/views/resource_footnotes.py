import logging
from flask import Blueprint
import datetime
import json

import ckan.lib.base as base
import ckan.model as model
import ckan.logic as logic
from ckan.common import g, request

from ckanext.bankofengland import helpers as boe_helpers

log = logging.getLogger(__name__)


boe_resource = Blueprint('boe_resource', __name__, url_prefix='/dataset/<id>/resource/<resource_id>')


def _get_context():
    context = {
        'model': model,
        'session': model.Session,
        'user': g.user,
        'auth_user_obj': g.userobj
    }

    return context


def footnotes(id, resource_id):
    log.error(request.args)
    log.error(request.form)
    log.error(request.method)
    log.error(request.data)
    context = _get_context()
    log.error(resource_id)

    pkg_dict = logic.get_action('package_show')(context, {'id': id})
    resource = logic.get_action('resource_show')(context, {'id': resource_id})
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
                            'column': resource.get('name')
                        }
                    )
                except Exception as e:
                    log.error(e)

        def _check_if_key_exists(key, dictionary):
            if key not in dictionary:
                dictionary[key] = {}

        footnotes = {}

        for key, value in req_form.items():
            if key.startswith('footnote-row-'):
                key = key.replace('footnote-row-', '')
                _check_if_key_exists(key, footnotes)
                footnotes[key]['row'] = value
            elif key.startswith('footnote-text-'):
                key = key.replace('footnote-text-', '')
                _check_if_key_exists(key, footnotes)
                footnotes[key]['text'] = value

        for key, value in footnotes.items():
            footnote = {
                'resource_id': resource_id,
                'row': value['row'],
                'column': resource.get('name'),
                'footnote': value['text']
            }

            try:
                logic.get_action('create_footnote')(
                    context, footnote
                )
            except Exception as e:
                log.error(e)
                try:
                    logic.get_action('update_footnote')(
                        context, footnote
                    )
                except Exception as e:
                    log.error(e)

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
