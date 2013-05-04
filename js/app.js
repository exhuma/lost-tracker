goog.provide('lost_tracker.app');

goog.require('goog.array');
goog.require('goog.dom');
goog.require('goog.dom.classlist');
goog.require('goog.dom.forms');
goog.require('goog.events');
goog.require('goog.events.EventType');
goog.require('goog.net.XhrIo');
goog.require('goog.style');


// This has to be set by flask template!
var $SCRIPT_ROOT;


/**
 * @constructor
 */
lost_tracker.app = function() {
};


lost_tracker.app.advanceState = function(event_source, groupId, stationId) {
  var container = event_source.parentNode;
  var elem = goog.dom.getElement(
    'icon_' + stationId + '_' + groupId);
  elem.src = $SCRIPT_ROOT + '/static/icons/loading.gif';
  goog.dom.classlist.removeAll(
      container, ['state_0', 'state_1', 'state_2']);
  goog.net.XhrIo.send(
      $SCRIPT_ROOT + '/advance/' + groupId + '/' + stationId,
      function(evt){
        var xhr = evt.target;
        if (xhr.isSuccess()){
          var data = xhr.getResponseJson();
          if (!goog.isDefAndNotNull(data.new_state)){
            return;
          }

          elem.src = $SCRIPT_ROOT + '/static/icons/' + data.new_state + '.png';
          goog.dom.classlist.add(container, 'state_' + data.new_state);
        } else {
          elem.src = $SCRIPT_ROOT + '/static/icons/status-warning.png';
        }
      });
};


/**
 * Attach events to the form elements.
 */
lost_tracker.app.attachEvents = function(stationId) {
  goog.array.forEach(goog.dom.getElementsByTagNameAndClass('div', 'group'),
      function(element) {
    var form = goog.dom.getElementsByTagNameAndClass('form', null, element)[0];
    var fields = form.elements;
    var initialFormData = goog.dom.forms.getFormDataMap(form);
    var icons = goog.dom.getElementsByTagNameAndClass('img', 'icon', element);

    goog.events.listen(fields['submit'], goog.events.EventType.CLICK, function(evt) {
      evt.preventDefault();
      var formData = goog.dom.forms.getFormDataMap(form);
      var formString = goog.dom.forms.getFormDataString(form);
      fields['station_score'].value = 0;
      fields['form_score'].value = 0;
      fields['station_score'].disabled = true;
      fields['form_score'].disabled = true;
      fields['submit'].disabled = true;
      var old_icon_source = icons[0].src;
      icons[0].src = $SCRIPT_ROOT + '/static/icons/loading.gif';
      goog.net.XhrIo.send(
          $SCRIPT_ROOT + '/score/' + formData.get('group_id'),
          function(evt){
            var xhr = evt.target;
            var data = xhr.getResponseJson();
            fields['station_score'].value = data.station_score;
            fields['form_score'].value = data.form_score;
            fields['station_score'].disabled = false;
            fields['form_score'].disabled = false;
            fields['submit'].disabled = false;
            icons[0].src = old_icon_source;
          }, 'POST', formString, {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          });
    });

    // Handle clicks on the icon
    goog.events.listen(icons[0], goog.events.EventType.CLICK, function(evt) {
      lost_tracker.app.advanceState(evt.target,
                                    initialFormData.get('group_id')[0],
                                    initialFormData.get('station_id')[0]);
    });

    // Handle the selection of a new form.
    goog.events.listen(fields['form_id'], goog.events.EventType.CHANGE, function(evt) {
      var formData = goog.dom.forms.getFormDataMap(evt.target.form);
      lost_tracker.app.getFormScore(
        formData.get('group_id'),
        formData.get('form_id'),
        fields['form_score']);
    });
  });

  goog.array.forEach(goog.dom.getElementsByTagNameAndClass('img', 'icon'),
      function(element) {
        goog.style.setHeight(element, 64);
        goog.style.setWidth(element, 64);
  });
};


/**
 * Get the form score for a group, and update the value of a specific elemnt
 */
lost_tracker.app.getFormScore = function(group_id, form_id, element) {
  goog.net.XhrIo.send(
      $SCRIPT_ROOT + '/score/' + group_id + '/' + form_id,
      function(evt){
        var xhr = evt.target;
        var data = xhr.getResponseJson();
        element.value = data.score;
      }, 'GET', null, {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      });
};


/**
 * Replace the "sum" elements by grpahs.
 */
lost_tracker.app.drawSums = function(stationId) {
  var table = goog.dom.getElement('Matrix');
  var head = goog.dom.getElementsByTagNameAndClass('thead', null, table)[0];
  var foot = goog.dom.getElementsByTagNameAndClass('tfoot', null, table)[0];
  var topSumRow = goog.dom.getLastElementChild(head);
  var topSums = goog.dom.getElementsByTagNameAndClass('td', null, topSumRow);
  topSums = goog.array.toArray(topSums)

  // ignore the first column in the row (the "title")
  topSums.shift();

  // no loop over the remaining columns.
  goog.array.forEach(topSums, function(element) {
    var spans = goog.dom.getElementsByTagNameAndClass('span', null, element);
    var unknown = spans[0].innerHTML;
    var arrived = spans[1].innerHTML;
    var finished = spans[2].innerHTML;
    // TODO: draw canvas
  });

};


goog.exportSymbol('lost_tracker.app.attachEvents',
    lost_tracker.app.attachEvents);

goog.exportSymbol('lost_tracker.app.drawSums',
    lost_tracker.app.drawSums);
