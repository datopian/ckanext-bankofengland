import click
import logging

import ckanext.bankofengland.model as boe_model

log = logging.getLogger(__name__)


@click.group()
def boe():
    """
    Bank of England commands
    """
    pass


@boe.command()
def initdb():
    """
    Initialize the Bank of England custom tables
    """
    boe_model.init_footnotes_table()


@boe.command()
def dropdb():
    """
    Drop the Bank of England custom tables

    WARNING: This is only intended for use in development environments
    """
    confirmation = click.prompt('Are you sure you want to drop the database? (y/n)')

    if confirmation.lower() == 'y':
        boe_model.remove_footnotes_table()
    else:
        click.echo('Database not dropped')


@boe.command()
@click.argument('resource_name')
def getfootnotes(resource_name):
    """
    Get the footnotes for a resource
    """
    footnotes = boe_model.get_footnotes(resource_name)

    for footnote in footnotes:
        click.echo(footnote)


@boe.command()
@click.option('--footnote_id', required=False)
@click.option('--row', required=False)
@click.option('--column', required=False)
def updatefootnote(footnote_id, row, column):
    """
    Update a footnote
    """

    if not footnote_id and (not row or not column):
        click.echo('Either a footnote_id or a row and column must be provided')
        return

    footnote_text = click.prompt('Enter the footnote text')

    if footnote_id:
        boe_model.update_footnote(footnote_id, footnote=footnote_text)
    else:
        boe_model.update_footnote(row=row, column=column, footnote=footnote_text)


@boe.command()
def addfootnote():
    """
    Add a footnote to the resource_footnotes table
    """
    #row_string = click.prompt('Enter the row date (dd mmm yy)')
    #row = datetime.datetime.strptime(row_string, '%d %b %y')
    #column = click.prompt('Enter the column name')
    #footnote_text = click.prompt('Enter the footnote text')
    #footnote_type = click.prompt('Enter the footnote type')
    resource_id = None
    row = None
    column = None
    footnote = None

    boe_model.add_footnote(resource_id, row, column, footnote)


def get_commands():
    return [boe]
