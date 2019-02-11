require.config({
    baseUrl: '/static',
    paths: {
        'jQuery': '//cdnjs.cloudflare.com/ajax/libs/jquery/2.2.0/jquery.min',
        'bootstrap': '//cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.6/js/bootstrap.min',
        'lodash':'//cdnjs.cloudflare.com/ajax/libs/lodash.js/4.5.1/lodash.min',
        'moment': '//cdnjs.cloudflare.com/ajax/libs/moment.js/2.9.0/moment.min',
        'datatables': '//cdnjs.cloudflare.com/ajax/libs/datatables/1.10.12/js/jquery.dataTables.min',
        'datatables.bootstrap': '//cdnjs.cloudflare.com/ajax/libs/datatables/1.10.11/js/dataTables.bootstrap.min',
        'datatables.datetime': '//cdn.datatables.net/plug-ins/1.10.11/sorting/datetime-moment',
        'bootstrap-datetimepicker': '//cdnjs.cloudflare.com/ajax/libs/bootstrap-datetimepicker/4.17.37/js/bootstrap-datetimepicker.min',
        'select2': '//cdnjs.cloudflare.com/ajax/libs/select2/3.5.4/select2.min',
    },
    map: {
        '*': {
            'jquery': 'jQuery',
            'datatables.net': 'datatables' // some datatables modules use the name datatables.net in their requirements
        }
    },
    shim: {
        'jQuery': {
            exports: '$'
        },
        'lodash': {
            exports: '_'
        },
        'bootstrap': {
            deps: ['jQuery']
        },
        'datatables': {
            deps: ['jQuery']
        },
        'datatables.bootstrap': {
            deps: ['jQuery', 'datatables']
        },
        'bootstrap-datetimepicker': {
            deps: ['jQuery', 'bootstrap', 'moment']
        },
        'select2': {
            deps: ['jQuery', 'bootstrap']
        }
    }
});
