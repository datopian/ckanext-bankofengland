import datetime
import logging

from ckan.plugins import toolkit


log = logging.getLogger(__name__)


def get_current_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def get_current_datetime():
    return datetime.datetime.now()


def get_resource_publish_date(date, time):
    log.error(type(date))
    log.error(type(time))
    # 'date' and 'time' are strings. We need to combine them into a datetime
    # object.
    # The 'date' string is in the format 'YYYY-MM-DD'.
    # The 'time' string is in the format 'HH:MM'.

    return datetime.datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M")


def filter_unpublished_resources(data_dict):
    resources = data_dict.get('resources', [])
    public_resources = []
    log.error('========================================')

    for resource in resources:
        publish_date = resource.get('publish_date', None)
        publish_time = resource.get('publish_time', None)

        if publish_date and publish_time:
            target_time = get_resource_publish_date(
                publish_date, publish_time
            )
            current_time = get_current_datetime()

            if target_time <= current_time:
                public_resources.append(resource)

    data_dict['resources'] = public_resources

    return data_dict
