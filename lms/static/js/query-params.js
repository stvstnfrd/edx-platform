(function (window) {
    var openedx;
    var utilities;
    function getParameterByName(name) {
        // http://james.padolsey.com/javascript/bujs-1-getparameterbyname/
        var match = RegExp('[?&]' + name + '=([^&]*)')
                        .exec(window.location.search);

        return match ?
            decodeURIComponent(match[1].replace(/\+/g, ' '))
            : null;
    }

    window = window || {};
    openedx = window.openedx || {};
    utilities = openedx.utilities = openedx.utilities || {};
    utilities.getParameterByName = getParameterByName;
    window.openedx = openedx;
}(window));
