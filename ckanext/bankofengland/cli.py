import click
from ckanext.bankofengland.model import init_footnotes_table, remove_footnotes_table, get_footnotes, add_footnote


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
    init_footnotes_table()


@boe.command()
def dropdb():
    """
    Drop the Bank of England custom tables

    WARNING: This is only intended for use in development environments
    """
    confirmation = click.prompt('Are you sure you want to drop the database? (y/n)')

    if confirmation.lower() == 'y':
        remove_footnotes_table()
    else:
        click.echo('Database not dropped')


@boe.command()
@click.argument('resource_name')
def footnotes(resource_name):
    """
    Get the footnotes for a resource
    """
    footnotes = get_footnotes(resource_name)

    for footnote in footnotes:
        click.echo(footnote)


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
    row = None
    column = None
    footnote_text = None

    add_footnote(row, column, footnote_text)


def get_commands():
    return [boe]
