$(document).ready(function() {
  $.tablesorter.themes.bootstrap.sortNone = 'fa fa-sort';
  $.tablesorter.themes.bootstrap.sortAsc = 'fa fa-sort-asc';
  $.tablesorter.themes.bootstrap.sortDesc = 'fa fa-sort-desc';
  $.tablesorter.themes.bootstrap.table= 'table table-condensed';
  $.extend(true, $.tablesorter.defaults, {
    theme: 'bootstrap',
    headerTemplate: '{content} {icon}',
    widgets: ['uitheme', 'pager', 'zebra', 'filter'],
    widgetOptions: {
      zebra: ['even', 'odd'],
      pager_output: ' of {totalPages}',
      pager_size: 10,
      pager_selectors: {
        first: '.page-first',
        prev: '.page-prev',
        next: '.page-next',
        last: '.page-last',
        gotoPage: '.page-goto',
        pageDisplay: '.page-display',
        pageSize: '.page-size'
      },
      filter_cssFilter: 'form-control'
    }
  });
});

