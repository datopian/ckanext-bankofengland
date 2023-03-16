
$(document).ready(function() {
    disableRows();
});

$('#footnote-table').change(function() {
    disableRows();
});

$('#save-footnotes').click(function(e) {
    e.preventDefault();
    var allFilled = false;
    var allRows = $('.footnote-row');
    var allColumns = $('.footnote-column');
    var allFootnotes = $('.footnote-text');
    var tableRows = $('#footnote-table > tbody > tr');

    for (var i = 0; i < tableRows.length; i++) {
        if (allRows[i].value == '' || allColumns[i].value == '' || allFootnotes[i].value == '') {
            allFilled = false;

            if (allRows[i].value == '') {
                $(allRows[i]).css('border', '1px solid red');
                $(allRows[i]).css('background-color', 'white');
            }
            if (allColumns[i].value == '') {
                $(allColumns[i]).css('border', '1px solid red');
            }
            if (allFootnotes[i].value == '') {
                $(allFootnotes[i]).css('border', '1px solid red');
            }
            break;
        } else {
            allFilled = true;
        }
    }

    if (!allFilled) {
        return;
    }

    $('#save-footnotes').prop('disabled', true);
    $('[id^=delete-footnote-row-]').prop('disabled', true);
    $('#save-footnotes').html('Saving...');
    $('#footnote-form').submit();
});

$('#add-footnote').click(function() {
    var rowValues = get_footnote_dropdown_options();
    var newUUID = uuidv4();

    var newRow = $('<tr>');
    var newSelect = $('<select>', {
        class: 'footnote-row',
        name: 'footnote-row-' + newUUID + '-new',
        id: 'footnote-row-' + newUUID + '-new',
        style: 'max-width: 100%;'
    });

    for (var i = 0; i < rowValues.length; i++) {
        let newOption = $('<option>', {
            class: 'footnote-row-option',
            value: rowValues[i],
            text: rowValues[i],
        });
        newSelect.append(newOption);
    }

    newSelect.prepend($('<option>', {
        class: 'footnote-row-option',
        value: '',
        text: '',
        selected: true,
    }));

    var pkgName = $('#pkg-name').val();

    newColumn = $('<td>').append($('<input>', {
        class: 'footnote-column',
        type: 'text',
        name: 'footnote-column-' + newUUID + '-new',
        id: 'footnote-column-' + newUUID + '-new',
        value: pkgName,
        style: 'max-width: 100%;'
    }));

    var newFootnote = $('<td>').append($('<textarea>', {
        class: 'footnote-text',
        value: '',
        rows: 2,
        name: 'footnote-text-' + newUUID + '-new',
        id: 'footnote-text-' + newUUID + '-new',
        style: 'width: 100%;'
    }));

    var newDeleteButton = $('<td>').append($('<button>', {
        class: 'btn btn-danger',
        type: 'button',
        id: 'delete-footnote-row-' + newUUID + '-new',
        data: JSON.stringify({
            'row': '',
            'text': '',
        }),
        text: 'Delete'
    }));

    newRow.append($('<td>').append(newSelect));
    newRow.append(newColumn);
    newRow.append(newFootnote);
    newRow.append(newDeleteButton);

    $('table > tbody').prepend(newRow);

    disableRows();
});

$('[id^=delete-footnote-row-]').click(function() {
    deleteRow($(this));
});

$('#footnote-table').click(function() {
    var sourceID = event.target.id;

    // If the user clicked on a row, column or footnote, remove the border (back to normal)
    if (sourceID.includes('footnote-row-')) {
        $('#' + sourceID).css('border', '1px solid #ccc');
        $('#' + sourceID).css('background-color', 'white');
    }
    if (sourceID.includes('footnote-column-')) {
        $('#' + sourceID).css('border', '1px solid #ccc');
    }
    if (sourceID.includes('footnote-text-')) {
        $('#' + sourceID).css('border', '1px solid #ccc');
    }

    if (sourceID.includes('delete-footnote-row-')) {
        deleteRow($('#' + sourceID));
    }
});


function deleteRow(row) {
    var rowFullID = row.attr('id');

    if (rowFullID == undefined) {
        return;
    }

    var newRow = false;

    if (rowFullID.endsWith('-new')) {
        newRow = true;
        if (rowFullID.startsWith('delete-footnote-row-')) {
            $('#footnote-row-' + rowID + '-new').parent().parent().remove();
        } else {
            row = row.replace('-new', '');
        }
    }

    var rowID = row.attr('id').replace('delete-footnote-row-', '');
    var rowData = row.attr('data');

    if (rowData !== undefined) {
        rowData = JSON.parse(rowData);

        var selectedValue = $('#footnote-row-' + rowID).find('option:selected').text();

        rowData['row'] = selectedValue;

        var currentFootnoteRows = $('#footnote-rows-deleted').val();

        if (currentFootnoteRows == undefined || currentFootnoteRows == '') {
            currentFootnoteRows = [];
        } else {
            currentFootnoteRows = JSON.parse(currentFootnoteRows);
        }

        currentFootnoteRows.push(rowData);
        $('#footnote-rows-deleted').val(JSON.stringify(currentFootnoteRows));
    }

    $('#footnote-row-' + rowID).parent().parent().remove();
}

function disableRows() {
    var selectedRows = [];

    $('.footnote-row').each(function() {
        selectedRows.push($(this).find('option:selected').text());
    });

    $('.footnote-row').each(function() {
        $(this).find('option').each(function() {
            if (selectedRows.includes($(this).text()) && !$(this).is(':selected')) {
                $(this).prop('disabled', true);
            } else {
                $(this).prop('disabled', false);
            }
        });
    });
}

function get_footnote_dropdown_options() {
    var rowsList = $('#footnote-rows-list').val();
    var rows = JSON.parse(rowsList);

    return rows;
}

function uuidv4() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
      (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
  }