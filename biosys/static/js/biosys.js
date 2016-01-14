var biosys = biosys || {};


biosys.dataTable = (function ($, _) {
    'use strict';

    var defaultOptions = {
        paging: true,
        info: true,
        searching: true,
        scrollCollapse: true,
        processing: true,
        deferRender: true,
        autowidth: true
    };

    function decorateTable(table) {
        // add the populate and fetch method
        table.get_data_fields = function () {
            return this.settings()[0][("aoColumns")].map(function (x) {
                return x.data;
            });
        };
        // Check that all column values are there.
        // Missing values are added as ''
        table.validate_row = function (row) {
            var fields = table.get_data_fields(),
                missing_columns = fields.filter(function (x) {
                    var is_dot_notation = _.contains(x, '.'); // don't support dot notation
                    return !is_dot_notation && row[x] === undefined;
                }),
                column_filler = {},
                column,
                i;

            for (i = 0; i < missing_columns.length; i += 1) {
                column = missing_columns[i];
                column_filler[column] = '';
            }
            return $.extend(row, column_filler);
        };

        table.populate = function (json) {
            var data = [];
            if (json) {
                if (typeof json === 'string') {
                    data = $.parseJSON(json);
                } else {
                    data = json;
                }
                var rows = data.map(table.validate_row);
                table.rows.add(rows).draw();
            }
        };

        table.fetch = function (url) {
            $.ajax({
                url: url,
                dataType: 'json',
                success: function (data) {
                    table.populate(data);
                }
            });
        };

        return table;
    }

    return {
        initTable: function (selector, tableOptions, columnsOptions) {
            var options = {},
                table;
            $.fn.DataTable.ext.errMode = "throws";  // will throw a console error instead of an alert
            $.extend(options, defaultOptions, tableOptions, {columns: columnsOptions});
            table = $(selector).DataTable(options);
            // add some methods
            table = decorateTable(table);
            return table;
        }
    }
})($, _);


