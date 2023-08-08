(function($) {
    'use strict';

    // Painel Gestao Configuration File
    var prefix = '/';
    var app = null;

    var config = {
        host: QLIK_HOST,
        prefix: prefix,
        port: parseInt(QLIK_PORT),
        isSecure: (QLIK_IS_SECURE.toLowerCase() === 'true')
    };

    require.config({
        baseUrl: (config.isSecure ? "https://" : "http://") + config.host + (config.port ? ":" + config.port : "") + config.prefix + "resources",
    });

    require(["js/qlik"], function(qlik) {        
        qlik.setOnError(function(error) {  
            console.log(error.getMessage());                                    
        });

        app = qlik.openApp(QLIK_APP_ID, config);

        // barra selecao
        app.getObject('CurrentSelections', 'CurrentSelections');

        // Carrega os objetos em tela
        load_objects();

        django.app.app = app;

        // Carrega os parâmetros que serão utilizados para realizar o filtro
        get_param_filters();      
    });

    // Sets the javascript request as synchronous
    $.ajaxSetup({async: false});

    // Get Qlik objects from json file
    var objetosQlik = (function() {
        var result;

        $.getJSON("/static/app/data/objetosQlik.json", {}, function(data) {
            result = data;
        });
        return result;
    })();

    // Returns the javascript request as asynchronous again
    $.ajaxSetup({async: true});

    function get_indice(id) {
        for (var x in objetosQlik) {
            if(objetosQlik[x].id == id) {
                return x;
            }
        }
    }

    function load_qlik_objects(qlikID) {    
        
        if(objetosQlik[get_indice(qlikID)]=== undefined || objetosQlik[get_indice(qlikID)] === null) {
            console.log('Objeto não encontrado: ' + qlikID);
        }
        
        app.visualization.get(objetosQlik[get_indice(qlikID)].codigo).then(function(vis) {                   
            vis.show(qlikID);
        });
    }    

    function load_objects() {
        var objetosQlikArray = [            
            'cidadao-qtd-forca-de-trabalho-por-sexo-graph',                    
        ];

        // iterate to get qlik objects
        for (var i = 0; i < objetosQlikArray.length; i++) {            
            load_qlik_objects(objetosQlikArray[i]);
        }
    }

    function get_param_filters() {
        var url_string = window.location.href;
        var params = url_string.split('?')[1];

        params = decodeURI(params);
        params = params.split('&');

        if(params[0] != 'undefined') {
            for(var i=0; i < params.length; i++) {
                var parameter = params[i].split('=');
                if(parameter[1]) {
                    var parameter_value = parameter[1].split(',');

                    if((parameter[0] == 'TEMPO_ANO')) {
                        applyFilter(parameter[0], parameter_value);
                    }
                }
            }
        }
    }

    function applyFilter(field, value) {
        app.field(field).selectValues(value, true, true);
    }

    django.app.objetosQlik = objetosQlik;
    django.app.get_indice = get_indice;
})(django.jQuery);
