(function($) {
    'use strict';

    // Check for the cookie when user first arrives, if cookie doesn't exist call the intro
    function get_cookie(c_name) {
        var c_value = document.cookie;
        var c_start = c_value.indexOf(" " + c_name + "=");

        if (c_start == -1) {
            c_start = c_value.indexOf(c_name + "=");
        }

        if (c_start == -1) {
            c_value = null;
        } else {
            c_start = c_value.indexOf("=", c_start) + 1;
            var c_end = c_value.indexOf(";", c_start);

            if (c_end == -1) {
                c_end = c_value.length;
            }

            c_value = unescape(c_value.substring(c_start, c_end));
        }

        return c_value;
    }

    // Set a specific cookie
    function set_cookie(c_name, value, exdays) {
        var exdate = new Date();
        exdate.setDate(exdate.getDate() + exdays);

        var c_value=escape(value) + ((exdays==null) ? "" : "; expires=" + exdate.toUTCString());
        document.cookie=c_name + "=" + c_value;
    }

    function get_url_params() {
        if (location.search != '') {
            var search = location.search.slice(1);
            return search.split('&')
        }
        return [];
    }

    function get_url_param(param) {
        var params = get_url_params();
        var param_value_returned = undefined;

        for (var index in params) {
            var key = params[index].split('=')[0];
            var value = params[index].split('=')[1];

            if (key === param) {
                param_value_returned = value;
                break;
            }
        }
        return param_value_returned;
    }

    // Função que inicia o preloading
    function start_preloading() {
        $('body').append("<div class='modal-backdrop fade show load-page'></div>")
                 .append("<div class='lds-css'><div class='ldio'><div></div><div></div><div></div><div></div></div></div>");
    };

    // Função que termina o preloading
    function stop_preloading() {
        $('.lds-css').remove();
        $('.load-page').remove();
        $('#posload').addClass('show');
    };
    
    $(document).ready(function() {
      // Código que deve ser executado logo quando inicia a aplicação
    });
    
    django.app.get_cookie = get_cookie;
    django.app.set_cookie = set_cookie;
    django.app.get_url_param = get_url_param;
    django.app.start_preloading = start_preloading;
    django.app.stop_preloading = stop_preloading;
    
})(django.jQuery);
