require.config({
    baseUrl: '/static',
    paths: {
        'jQuery': '//static.dpaw.wa.gov.au/static/libs/jquery/2.2.0/jquery.min',
        'bootstrap': '//static.dpaw.wa.gov.au/static/libs/twitter-bootstrap/3.3.6/js/bootstrap.min',
        'lodash':'//static.dpaw.wa.gov.au/static/libs/lodash.js/4.5.1/lodash.min',
        'moment': '//static.dpaw.wa.gov.au/static/libs/moment.js/2.9.0/moment.min',
        'datatables': '//static.dpaw.wa.gov.au/static/libs/datatables/1.10.12/js/jquery.dataTables.min',
        'datatables.bootstrap': '//static.dpaw.wa.gov.au/static/libs/datatables/1.10.11/js/dataTables.bootstrap.min',
        'datatables.datetime': '//cdn.datatables.net/plug-ins/1.10.11/sorting/datetime-moment',
        'bootstrap-datetimepicker': '//static.dpaw.wa.gov.au/static/libs/bootstrap-datetimepicker/4.17.37/js/bootstrap-datetimepicker.min',
        'select2': '//static.dpaw.wa.gov.au/static/libs/select2/3.5.4/select2.min',
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
