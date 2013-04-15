goog.provide('lost_tracker.app');

goog.require('goog.array');
goog.require('goog.dom');
goog.require('goog.dom.classlist');
goog.require('goog.dom.forms');
goog.require('goog.events');
goog.require('goog.events.EventType');
goog.require('goog.net.XhrIo');
goog.require('goog.style');


/**
 * @constructor
 */
lost_tracker.app = function() {
};


lost_tracker.app.advanceState = function(event_source, groupId, stationId) {
  var container = event_source.parentNode;
  var elem = goog.dom.getElement(
    'icon_' + stationId + '_' + groupId);
  elem.src = '/static/icons/loading.gif';
  goog.dom.classlist.removeAll(
      container, ['state_0', 'state_1', 'state_2']);
  goog.net.XhrIo.send(
      '/advance/' + groupId + '/' + stationId,
      function(evt){
        var xhr = evt.target;
        if (xhr.isSuccess()){
          var data = xhr.getResponseJson();
          if (!goog.isDefAndNotNull(data.new_state)){
            return;
          }

          elem.src = '/static/icons/' + data.new_state + '.png';
          goog.dom.classlist.add(container, 'state_' + data.new_state);
        } else {
          elem.src = '/static/icons/status-warning.png';
        }
      });
};


/**
 * Attach events to the form elements.
 */
lost_tracker.app.attachEvents = function(stationId) {
  goog.array.forEach(goog.dom.getElementsByTagNameAndClass('div', 'group'),
      function(element) {
    var form = goog.dom.getElementsByTagNameAndClass('form', null, element);
    var initialFormData = goog.dom.forms.getFormDataMap(form[0]);
    var submit_buttons = goog.array.filter(form[0], function(felement) {
      return felement.type == 'submit';
    });
    goog.events.listen(submit_buttons[0], goog.events.EventType.CLICK, function(evt) {
      var formData = goog.dom.forms.getFormDataMap(evt.target.form);
      var formString = goog.dom.forms.getFormDataString(evt.target.form);
      goog.net.XhrIo.send(
          '/score/' + formData.get('group_id'),
          function(evt){
            var xhr = evt.target;
            var data = xhr.getResponseJson();
          }, 'POST', formString, {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          });
      evt.preventDefault();
    });

    // Handle clicks on the icon
    var icons = goog.dom.getElementsByTagNameAndClass('img', 'icon', element);
    goog.events.listen(icons[0], goog.events.EventType.CLICK, function(evt) {
      lost_tracker.app.advanceState(evt.target,
                                    initialFormData.get('group_id')[0],
                                    initialFormData.get('station_id')[0]);
    });
  });

  goog.array.forEach(goog.dom.getElementsByTagNameAndClass('img', 'icon'),
      function(element) {
        goog.style.setHeight(element, 64);
        goog.style.setWidth(element, 64);
  });
};


goog.exportSymbol('lost_tracker.app.attachEvents',
    lost_tracker.app.attachEvents);
