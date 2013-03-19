goog.provide('tracker');

goog.require('goog.array');
goog.require('goog.dom');
goog.require('lost_tracker.model.Station');


/**
 * @constructor
 */
var tracker = function() {
  var groups = lost_tracker.model.Station.all();
  var cd = goog.dom.createDom;
  var content = goog.dom.getElement('content');

  goog.array.forEach(groups, function(group) {
    var groupDiv = cd('div', {'class': 'group_widget'},
      cd('div', {'class': 'ops'}, 'ops'),
      cd('div', {'class': 'group'}, '' + group));
    content.appendChild(groupDiv);
  });

};

goog.exportSymbol('tracker', tracker);
