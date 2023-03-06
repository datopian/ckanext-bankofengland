import datetime
import logging

from ckan.plugins import toolkit

log = logging.getLogger(__name__)

def tag_length_validator(value, context):
    return value

def tag_name_validator(value, context):
    return value

def only_future_date(value, context):
    if value:
        date = datetime.datetime.strptime(value, "%Y-%m-%d")
        current_date = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        log.error(date)
        log.error(current_date)

        if date < current_date:
            raise toolkit.Invalid("Date must be in the future")

    return value
