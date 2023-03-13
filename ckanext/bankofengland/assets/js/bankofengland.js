
$(document).ready(function() {
    disableRows();
});

$('.footnote-row').change(function() {
    disableRows();
});

$('#add-footnote').click(function() {
    var rowValues = get_footnote_dropdown_options();

    var newRow = $('<tr>');
    var newSelect = $('<select>', {
        class: 'footnote-row',
        name: 'footnote-row'
    });

    for (var i = 0; i < rowValues.length; i++) {
        let newOption = $('<option>', {
            value: rowValues[i],
            text: rowValues[i]
        });
        newSelect.append(newOption);
    }

    newSelect.prepend($('<option>', {
        value: '',
        text: ''
    }));

    var newColumn = $('<td>').append($('<input>', {
        type: 'text',
        name: 'column',
        value: ''
    }));

    var newFootnote = $('<td>').append($('<textarea>', {
        name: 'footnote-text',
        value: '',
        rows: 2
    }));

    newRow.append($('<td>').append(newSelect));
    newRow.append(newColumn);
    newRow.append(newFootnote);

    $('table > tbody').append(newRow);

    disableRows();
});

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