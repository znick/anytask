Placeholder text plugin for TinyMCE
===================================

This plugin brings HTML5 placeholder attribute functionality for the TinyMCE editor.

Usage
-----

* Add the plugin script to the page
* Add "placeholder" to tinymce config plugins array.
* Add a placeholder attribute to the textarea as usual or set placeholder property in editor settings.

Note: This plugin is not compatible with TinyMCE inline mode. It only works in classic mode.

Installation with bower
-------
To install plugin using bower use command <code>bower install tinymce-placeholder-attribute</code>

Example
-------

Tinymce Plugins Array:
plugins: "fullscreen placeholder"

Textarea:
`<textarea class="tinymce" placeholder="Hello World!"></textarea>`