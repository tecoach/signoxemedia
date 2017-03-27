(function () {
    const $ = django.jQuery;
    $(document).ready(function () {
        const wrappers = Array
            .from(document.querySelectorAll('.ace-code-editor'))
            .forEach((wrapper) => {
                const aceDiv = wrapper.querySelector('.editor');
                const textarea = wrapper.querySelector('textarea');
                require(["ace/ace"], function (ace) {
                    ace.require("ace/ext/language_tools");
                    const editor = ace.edit(aceDiv);
                    editor.setHighlightActiveLine(true);
                    editor.setTheme('ace/theme/github');
                    editor.session.setMode('ace/mode/html');
                    editor.session.setValue(textarea.value);
                    editor.setOption('maxLines', 30);
                    editor.setOption('minLines', 10);
                    editor.setOptions({
                        enableBasicAutocompletion: true,
                        enableSnippets: true,
                        enableLiveAutocompletion: false
                    });
                    editor.session.on('change', function () {
                        textarea.value = editor.session.getValue();
                    });
                });
            });
    });
})();
