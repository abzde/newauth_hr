from flask.ext.assets import Bundle
from webassets.filter.cssrewrite import CSSRewrite

from newauth.assets import assets_env

hr_js = Bundle(
    'hr/bower_components/tablesorter/js/jquery.tablesorter.js',
    'hr/bower_components/tablesorter/js/jquery.tablesorter.widgets.js',
    'hr/bower_components/tablesorter/js/widgets/widget-pager.js',
    'hr/../static/js/sorter.js',
    output='hr/js/hr.js'
)
assets_env.register('hr_js', hr_js)

hr_css = Bundle(
    'hr/bower_components/tablesorter/css/theme.bootstrap.css',
    'hr/bower_components/tablesorter/addons/pager/jquery.tablesorter.pager.js',
    'hr/../static/css/report.css',
    'hr/../static/css/sorter.css',
    output='hr/css/hr.css',
    filters=(CSSRewrite(
        replace=lambda url: '../bower_components/tablesorter/css/images/' + url))
)
assets_env.register('hr_css', hr_css)
