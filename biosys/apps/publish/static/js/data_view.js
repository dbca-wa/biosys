var biosys = biosys || {};

biosys.view_data = function ($, _, moduleOptions) {
    "use strict";
    var options = moduleOptions,
        selectors = options.selectors,
        data = options.data,
        $tablePanel = $(selectors.tablePanel),
        dataTable,
        datasets;

    function initProjectFilter() {
        var $select = $(selectors.projectFilter);
        $select.select2({
            placeholder: 'Select project',
            allowClear: true
        });
        $select.on('change', function (e) {
            var url = '/api/v2/dataset/?project__id=' + $(e.target).val();
            $.ajax(url, {
                    data: 'json'
                }
            ).then(function (data) {
                showDatasets(data.objects || []);
            });
        });
    }

    function showDatasets(dss) {
        var nodeTemplate = _.template(
            '<li role="presentation" id="id-nav-<%= name %>" data-view="<%= name %>" class=""><a href="#"><%= name %></a></li>'
            ),
            $navPanel = $(selectors.navPanel),
            $node;
        datasets = dss;
        $navPanel.children().remove();
        $tablePanel.children().remove();
        _.forEach(datasets, function (ds) {
            $node = $(nodeTemplate({name: ds.name}));
            $node.on('click', function (e) {
                showData($(e.target).parent().attr('data-view'));
            });
            $navPanel.append($node);
        });
    }

    function showData(name) {
        var ds = _.filter(datasets, function (ds) {
            return ds.name === name;
        }), headers, colDefs, $tableNode;
        $tablePanel.children().remove();
        $tableNode = $('<table id="data-table" class="table table-bordered table-responsive"></table>');
        $tablePanel.append($tableNode);
        if (ds.length > 0) {
            headers = _.map(ds[0].data_package.resources[0].schema.fields, function (field) {
                return field.name;
            });
            colDefs = _.map(headers, function (header) {
                return {
                    'title': header
                };
            });
            dataTable = biosys.dataTable.initTable($tableNode, {},  colDefs);
        }
    }

    return {
        init: function () {
            initProjectFilter();
            //$('select').select2();
        }
    };
};
