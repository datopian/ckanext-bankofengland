import datetime
import logging
import pytz


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

    data_dict['resources'] = public_resources

    return data_dict
