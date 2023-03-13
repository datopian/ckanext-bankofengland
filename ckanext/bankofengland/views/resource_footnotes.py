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
    context = _get_context()

    log.error(request.form)
    pkg_dict = logic.get_action('package_show')(context, {'id': id})
    resource = logic.get_action('resource_show')(context, {'id': resource_id})
    req_args = request.args
    resource_name = req_args.get('resource_name', resource.get('name'))

    if not resource_name:
        resource_name = resource_id
    else:
        resource_name = resource_name.lower()

    row_values = boe_helpers.get_footnote_rows(resource_name)

    existing_footnotes = logic.get_action('footnotes_show')(
        context, {'name': resource_name.upper()}
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
