goog.provide('tracker');

goog.require('goog.array');
goog.require('goog.dom');
goog.require('lost_tracker.model.Station');
goog.require('goog.fx.dom.ResizeWidth');
goog.require('goog.style');

/**
 * @constructor
 */
var tracker = function() {
  var groups = lost_tracker.model.Station.all();
  var cd = goog.dom.createDom;
  var content = goog.dom.getElement('content');

  goog.array.forEach(groups, function(group) {
    var ops = cd('div', {'class': 'ops'}, 'ops');
    var groupinfo = cd('div', {'class': 'group'}, '' + group);
    var groupDiv = cd('div', {'class': 'group_widget'},
      ops,
      groupinfo);
    content.appendChild(groupDiv);
    goog.events.listen(ops, goog.events.EventType.CLICK,
      function(evt) {
        var element = evt.target;
        var parent = goog.dom.getParentElement(element);
        var parsize = goog.style.getSize(parent);
        window['console']['log'](parsize)
        var elsize = goog.style.getSize(element);
        var anim = new goog.fx.dom.ResizeWidth(element,
          elsize.width,
          parsize.width,
          50);
        goog.style.setStyle(groupinfo, 'display', 'none');
        anim.play()
      }, false, this);
  });

};

goog.exportSymbol('tracker', tracker);
