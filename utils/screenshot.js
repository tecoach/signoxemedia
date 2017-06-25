/**
 * A phantomjs script to create a screenshot of a webpage and save it to a file.
 */
var page = require('webpage').create();
var system = require('system');

if (system.args.length !== 3) {
    console.log('Usage: screenshot.js <url> <filename>');
    phantom.exit();
}

var url = system.args[1];
var fileName = system.args[2];

page.viewportSize = {
    width: 1152,
    height: 648
};

page.clipRect = {
    top: 0,
    left: 0,
    width: 1152,
    height: 648
};

page.open(url, function () {
    page.evaluate(function () {
        var style = document.createElement('style'),
            text = document.createTextNode('body { background: #fff }');
        style.setAttribute('type', 'text/css');
        style.appendChild(text);
        document.head.insertBefore(style, document.head.firstChild);
    });
    page.render(fileName);
    phantom.exit();
});
