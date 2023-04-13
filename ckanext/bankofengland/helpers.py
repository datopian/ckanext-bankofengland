import datetime
import logging
import pytz
import json
import uuid

import ckan.plugins.toolkit as toolkit
import ckan.logic as logic


log = logging.getLogger(__name__)


def get_current_date():
    return datetime.datetime.now().strftime('%Y-%m-%d')


def get_current_datetime():
    return datetime.datetime.now(pytz.utc)


def filter_unpublished_resources(data_dict):
    resources = data_dict.get('resources', [])
    public_resources = []

    for resource in resources:
        publish_date = resource.get('publish_date', None)

        if publish_date:
            publish_date = datetime.datetime.strptime(
                publish_date, '%Y-%m-%dT%H:%M:%S'
            )
            publish_date = publish_date.astimezone(pytz.utc)

            current_date = get_current_datetime()

            if publish_date <= current_date:
                public_resources.append(resource)
        else:
            public_resources.append(resource)

    data_dict['resources'] = public_resources

    return data_dict


def get_footnote_rows(resource_id):
    rows = {'records': []}

    try:
        start = 0
        limit = 30000

        while True:
            rows_page = logic.get_action('datastore_search')({}, {
                'resource_id': resource_id,
                'limit': limit,
                'offset': start
            })

            rows['records'] += rows_page['records']

            if len(rows_page['records']) < limit:
                break

    except logic.NotFound:
        log.error('No resource found with name: {}'.format(resource_id))

    row_values = []

    if rows:
        records = rows.get('records', [])

        for row in records:
            row_date = row.get('Date')
            row_date = row_date.split('T')[0]

            if row_date:
                row_values.append(row_date)

    return row_values


def generate_uuid():
    return str(uuid.uuid4())


def to_json(data):
    if isinstance(data.get('row'), datetime.datetime):
        data['row'] = data['row'].strftime('%Y-%m-%d %H:%M:%S')

    return json.dumps(data)


def add_group_names_to_dropdown(group_dropdown):
    updated_group_dropdown = []
    for group in group_dropdown:
        group_dict = logic.get_action('group_show')({}, {'id': group[0]})
        updated_group_dropdown.append((group + [group_dict['name']]))

    return updated_group_dropdown
