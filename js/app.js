goog.provide('lost_tracker.app');

goog.require('goog.array');
goog.require('goog.dom');
goog.require('goog.dom.classlist');
goog.require('goog.dom.forms');
goog.require('goog.events');
goog.require('goog.events.EventType');
goog.require('goog.net.XhrIo');


/**
 * @constructor
 */
lost_tracker.app = function() {
};


lost_tracker.app.advanceState = function(event_source, groupId, stationId) {
  var container = event_source.parentNode.parentNode;
  goog.dom.classlist.removeAll(
      container, ['state_0', 'state_1', 'state_2']);
  goog.net.XhrIo.send(
      '/advance/' + groupId + '/' + stationId,
      function(evt){
        var xhr = evt.target;
        var data = xhr.getResponseJson();
        if (!goog.isDefAndNotNull(data.new_state)){
          return;
        }
        var elem = goog.dom.getElement(
          'icon_' + data.station_id + '_' + data.group_id);

        if (goog.isDefAndNotNull(elem)){
          elem.src = '/static/icons/' +
              data.new_state + '.png';
        }
        goog.dom.classlist.add(container, 'state_' + data.new_state);
      });
};


/**
 * Attach events to the form elements.
 */
lost_tracker.app.attachEvents = function(stationId) {
  goog.array.forEach(goog.dom.getElementsByTagNameAndClass('div', 'group'),
      function(element) {
    var form = goog.dom.getElementsByTagNameAndClass('form', null, element);
    var submit_buttons = goog.array.filter(form[0], function(felement) {
      return felement.type == 'submit';
    });
    goog.events.listen(submit_buttons[0], goog.events.EventType.CLICK, function(evt) {
      var formData = goog.dom.forms.getFormDataMap(evt.target.form);
      goog.net.XhrIo.send(
          '/group/' + formData.get('group_id')[0] + '/' + stationId,
          function(evt){
            var xhr = evt.target;
            var data = xhr.getResponseJson();
            window['console']['log'](data);
          }, 'POST',
          'score=' + formData.get('score')[0]);
      evt.preventDefault();
    });
  });
};


goog.exportSymbol('lost_tracker.app.attachEvents',
    lost_tracker.app.attachEvents);
goog.exportSymbol('lost_tracker.app.advanceState',
    lost_tracker.app.advanceState);
