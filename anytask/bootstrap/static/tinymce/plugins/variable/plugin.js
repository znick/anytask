/**
 * plugin.js
 */

/*global tinymce:true */

tinymce.PluginManager.add('variable', function (editor) {
    var each = tinymce.each;

    function createVariableList(callback) {
        return function () {
            var variableList = editor.settings.variables;
            callback(variableList);
        };
    }

    function showDialog(variableList) {
        var win, values = [], variableHtml;

        if (!variableList || variableList.length === 0) {
            var message = editor.translate('No variables defined.');
            editor.notificationManager.open({text: message, type: 'info'});
            return;
        }

        tinymce.each(variableList, function (variable) {
            values.push({
                selected: !values.length,
                text: variable.title,
                value: {
                    url: variable.url,
                    content: variable.content,
                    description: variable.description
                }
            });
        });

        function onSelectVariable(e) {
            var value = e.control.value();

            function insertIframeHtml(html) {
                if (html.indexOf('<html>') == -1) {
                    var contentCssLinks = '';

                    tinymce.each(editor.contentCSS, function (url) {
                        contentCssLinks += '<link type="text/css" rel="stylesheet" href="' + editor.documentBaseURI.toAbsolute(url) + '">';
                    });

                    var bodyClass = editor.settings.body_class || '';
                    if (bodyClass.indexOf('=') != -1) {
                        bodyClass = editor.getParam('body_class', '', 'hash');
                        bodyClass = bodyClass[editor.id] || '';
                    }

                    html = (
                        '<!DOCTYPE html>' +
                        '<html>' +
                        '<head>' +
                        contentCssLinks +
                        '</head>' +
                        '<body class="' + bodyClass + '">' +
                        html +
                        '</body>' +
                        '</html>'
                    );
                }

                var doc = win.find('iframe')[0].getEl().contentWindow.document;
                doc.open();
                doc.write(html);
                doc.close();
            }

            if (value.url) {
                tinymce.util.XHR.send({
                    url: value.url,
                    success: function (html) {
                        variableHtml = html;
                        insertIframeHtml(variableHtml);
                    }
                });
            } else {
                variableHtml = value.content;
                insertIframeHtml(variableHtml);
            }

            win.find('#description')[0].text(e.control.value().description);
        }

        win = editor.windowManager.open({
            title: 'Insert variable',
            layout: 'flex',
            direction: 'column',
            align: 'stretch',
            padding: 15,
            spacing: 10,

            items: [
                {
                    type: 'form', flex: 0, padding: 0, items: [
                    {
                        type: 'container', label: 'Variables', items: {
                        type: 'listbox', label: 'Variables', name: 'variable', values: values, onselect: onSelectVariable
                    }
                    }
                ]
                },
                {type: 'label', name: 'description', label: 'Description', text: '\u00a0'},
                {type: 'iframe', flex: 1, border: 1}
            ],

            onsubmit: function () {
                insertVariable(false, variableHtml);
            },

            minWidth: Math.min(tinymce.DOM.getViewPort().w, editor.getParam('variable_popup_width', 300)),
            minHeight: Math.min(tinymce.DOM.getViewPort().h, editor.getParam('variable_popup_height', 210))
        });

        win.find('listbox')[0].fire('select');
    }

    function insertVariable(ui, html) {
        var el, n, dom = editor.dom, sel = editor.selection.getContent();

        el = dom.create('div', null, html);

        // Find variable element within div
        n = dom.select('.mceTmpl', el);
        if (n && n.length > 0) {
            el = dom.create('div', null);
            el.appendChild(n[0].cloneNode(true));
        }

        function hasClass(n, c) {
            return new RegExp('\\b' + c + '\\b', 'g').test(n.className);
        }

        each(dom.select('*', el), function (n) {
            // Replace selection
            if (hasClass(n, editor.getParam('variable_selected_content_classes', 'selcontent').replace(/\s+/g, '|'))) {
                n.innerHTML = sel;
            }
        });

        editor.execCommand('mceInsertContent', false, el.innerHTML);
        editor.addVisual();
    }

    editor.addCommand('mceInsertVariable', insertVariable);

    editor.addButton('variable', {
        title: 'Insert variable',
        icon: 'template',
        onclick: createVariableList(showDialog)
    });

    editor.addMenuItem('variable', {
        text: 'Variable',
        onclick: createVariableList(showDialog),
        context: 'insert'
    });
});
