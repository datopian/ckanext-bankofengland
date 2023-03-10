import logging
from sqlalchemy import MetaData, Table, Column, types
import ckan.model as model
from ckan.model import meta, types as _types, User
import datetime


log = logging.getLogger(__name__)


def init_footnotes_table():
    if not model.meta.engine.has_table('resource_footnotes'):
        metadata = MetaData()

        Table('resource_footnotes', metadata,
            Column('id', types.UnicodeText,
                primary_key=True, default=_types.make_uuid,
                nullable=False, unique=True),
            Column('row', types.DateTime, nullable=False),
            Column('column', types.UnicodeText, nullable=False),
            Column('footnote', types.UnicodeText, nullable=False)
        )

        metadata.create_all(model.meta.engine)

        log.info('Created table resource_footnotes')
    else:
        log.info('Table resource_footnotes already exists')


def get_footnotes(resource_name):
    table = get_table('resource_footnotes')
    query = table.select(table.c.column == resource_name)
    result = model.meta.engine.execute(query)
    # Convert to a list of dicts
    result = [dict(row) for row in result]
    return result


def add_footnote(row, column, footnote):
    table = get_table('resource_footnotes')
    row_string = "30 Sep 19"
    row = datetime.datetime.strptime(row_string, '%d %b %y')
    column = 'DPQTADJ'
    footnote = 'This is a test'

    query = table.insert().values(
        id=_types.make_uuid(),
        row=row,
        column=column,
        footnote=footnote
    )

    model.meta.engine.execute(query)
    log.info('Added footnote to resource_footnotes table')


def delete_footnote(footnote_id, row=None, column=None):
    table = get_table('resource_footnotes')

    try:
        if footnote_id:
            query = table.delete().where(
                table.c.id == footnote_id
            )
        elif row and column:
            query = table.delete().where(
                table.c.row == row,
                table.c.column == column
            )
        else:
            raise Exception('Must provide either a footnote_id or a row and column')

        model.meta.engine.execute(query)

        log.info('Deleted footnote from resource_footnotes table')
    except Exception as e:
        log.error('Error deleting footnote: {}'.format(e))


def get_table(table_name):
    metadata = MetaData()
    metadata.reflect(bind=model.meta.engine)
    table = metadata.tables[table_name]
    return table


def remove_footnotes_table():
    if model.meta.engine.has_table('resource_footnotes'):
        metadata = MetaData()

        Table('resource_footnotes', metadata,
            Column('id', types.UnicodeText,
                primary_key=True, default=_types.make_uuid,
                nullable=False, unique=True),
            Column('row', types.DateTime, nullable=False),
            Column('column', types.UnicodeText, nullable=False),
            Column('footnote_text', types.UnicodeText, nullable=False),
            Column('footnote_type', types.UnicodeText, default=''),
        )

        metadata.drop_all(model.meta.engine)

        log.info('Dropped table resource_footnotes')
    else:
        log.info('Table resource_footnotes does not exist')
