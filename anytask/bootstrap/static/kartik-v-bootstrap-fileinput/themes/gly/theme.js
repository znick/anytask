/*!
 * bootstrap-fileinput v4.3.9
 * http://plugins.krajee.com/file-input
 *
 * Glyphicon (default) theme configuration for bootstrap-fileinput.
 *
 * Author: Kartik Visweswaran
 * Copyright: 2014 - 2017, Kartik Visweswaran, Krajee.com
 *
 * Licensed under the BSD 3-Clause
 * https://github.com/kartik-v/bootstrap-fileinput/blob/master/LICENSE.md
 */
(function ($) {
    "use strict";

    $.fn.fileinputThemes.gly = {
        fileActionSettings: {
            removeIcon: '<i class="glyphicon glyphicon-trash text-danger"></i>',
            uploadIcon: '<i class="glyphicon glyphicon-upload text-info"></i>',
            zoomIcon: '<i class="glyphicon glyphicon-zoom-in"></i>',
            dragIcon: '<i class="glyphicon glyphicon-menu-hamburger"></i>',
            indicatorNew: '<i class="glyphicon glyphicon-hand-down text-warning"></i>',
            indicatorSuccess: '<i class="glyphicon glyphicon-ok-sign text-success"></i>',
            indicatorError: '<i class="glyphicon glyphicon-exclamation-sign text-danger"></i>',
            indicatorLoading: '<i class="glyphicon glyphicon-hand-up text-muted"></i>'
        },
        layoutTemplates: {
            fileIcon: '<i class="glyphicon glyphicon-file kv-caption-icon"></i>'
        },
        previewZoomButtonIcons: {
            prev: '<i class="glyphicon glyphicon-triangle-left"></i>',
            next: '<i class="glyphicon glyphicon-triangle-right"></i>',
            toggleheader: '<i class="glyphicon glyphicon-resize-vertical"></i>',
            fullscreen: '<i class="glyphicon glyphicon-fullscreen"></i>',
            borderless: '<i class="glyphicon glyphicon-resize-full"></i>',
            close: '<i class="glyphicon glyphicon-remove"></i>'
        },
        previewFileIcon: '<i class="glyphicon glyphicon-file"></i>',
        browseIcon: '<i class="glyphicon glyphicon-folder-open"></i>&nbsp;',
        removeIcon: '<i class="glyphicon glyphicon-trash"></i>',
        cancelIcon: '<i class="glyphicon glyphicon-ban-circle"></i>',
        uploadIcon: '<i class="glyphicon glyphicon-upload"></i>',
        msgValidationErrorIcon: '<i class="glyphicon glyphicon-exclamation-sign"></i> '
    };
})(window.jQuery);
