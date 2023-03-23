import logging
from sqlalchemy import MetaData, Table, Column, types
import ckan.model as model
from ckan.model import types as _types
import datetime


log = logging.getLogger(__name__)


def init_footnotes_table():
    if not model.meta.engine.has_table('resource_footnotes'):
        metadata = MetaData()

        Table('resource_footnotes', metadata,
            Column('id', types.UnicodeText,
                primary_key=True, default=_types.make_uuid,
                nullable=False, unique=True),
            Column('resource_id', types.UnicodeText, nullable=False),
            Column('row', types.UnicodeText, nullable=True),
            Column('column', types.UnicodeText, nullable=False),
            Column('footnote', types.UnicodeText, nullable=False)
        )

        metadata.create_all(model.meta.engine)

        log.info('Created table resource_footnotes')
    else:
        log.info('Table resource_footnotes already exists')


def get_footnotes(footnote_id=None, resource_id=None):
    table = get_table('resource_footnotes')

    if resource_id:
        query = table.select(table.c.resource_id == resource_id)
    elif footnote_id:
        query = table.select(table.c.id == footnote_id)
    else:
        log.error('No resource name or id provided')
        return []

    result = model.meta.engine.execute(query)
    result = [dict(row) for row in result]

    return result


def create_footnote(resource_id, row, column, footnote):
    table = get_table('resource_footnotes')

    if not all([resource_id, column, footnote]):
        log.error('Failed to create footnote. Missing required fields.')
        return

    query = table.insert().values(
        id=_types.make_uuid(),
        resource_id=resource_id,
        row=row,
        column=column,
        footnote=footnote
    )

    model.meta.engine.execute(query)
    log.info('Added footnote to resource_footnotes table')


def delete_footnote(footnote_id=None):
    table = get_table('resource_footnotes')

    try:
        if footnote_id:
            query = table.delete().where(
                table.c.id == footnote_id
            )
        else:
            raise Exception(
                'Failed to delete footnote from resource_footnotes table.\n'
                'You must provide footnote_id'
            )

        model.meta.engine.execute(query)

        log.info('Deleted footnote from resource_footnotes table')
    except Exception as e:
        log.error('Error deleting footnote: {}'.format(e))


def footnote_exists(footnote_id=None, resource_id=None, row=None, column=None, footnote=None):
    table = get_table('resource_footnotes')

    try:
        if footnote_id:
            query = table.select(table.c.id == footnote_id)
        elif resource_id and (row is not None):
            query = table.select(
                (table.c.resource_id == resource_id) &
                (table.c.row == row) &
                (table.c.footnote == footnote)
            )
        elif (row is not None) and column and footnote:
            query = table.select(
                (table.c.row == row) &
                (table.c.column == column) &
                (table.c.footnote == footnote)
            )
        else:
            raise Exception(
                'Failed to check if footnote exists in resource_footnotes table.\n'
                'You must provide one of the following:\n'
                '- footnote_id\n'
                '- resource_id and row\n'
                '- row and column'
            )

        result = model.meta.engine.execute(query)
        result = [dict(res_row) for res_row in result]

        for res_row in result:
            if res_row['resource_id'] == resource_id and res_row['row'] == row and res_row['column'] == column and res_row['footnote'] == footnote:
                return True
            else:
                return False

        return False
    except Exception as e:
        log.error('Error checking if footnote exists: {}'.format(e))


def update_footnote(footnote_id=None, resource_id=None, row=None, column=None, footnote=None):
    table = get_table('resource_footnotes')

    try:
        if footnote_id:
            query = table.update().where(
                table.c.id == footnote_id
            ).values(
                row=row,
                column=column,
                footnote=footnote
            )
        else:
            raise Exception(
                'Failed to update footnote in resource_footnotes table.\n'
                'You must provide footnote_id'
            )

        model.meta.engine.execute(query)

        log.info('Updated footnote in resource_footnotes table')
    except Exception as e:
        log.error('Error updating footnote: {}'.format(e))


def get_table(table_name):
    metadata = MetaData()
    metadata.reflect(bind=model.meta.engine)
    table = metadata.tables[table_name]
    return table


# Note: this is currently only for testing purposes
def remove_footnotes_table():
    if model.meta.engine.has_table('resource_footnotes'):
        metadata = MetaData()

        Table('resource_footnotes', metadata,
            Column('id', types.UnicodeText,
                primary_key=True, default=_types.make_uuid,
                nullable=False, unique=True),
            Column('row', types.UnicodeText, nullable=True),
            Column('column', types.UnicodeText, nullable=False),
            Column('footnote_text', types.UnicodeText, nullable=False),
        )

        metadata.drop_all(model.meta.engine)

        log.info('Dropped table resource_footnotes')
    else:
        log.info('Table resource_footnotes does not exist')
