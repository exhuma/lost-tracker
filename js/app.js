goog.provide('lost_tracker.app');

goog.require('goog.dom');
goog.require('goog.dom.classlist');
goog.require('goog.net.XhrIo');


/**
 * @constructor
 */
lost_tracker.app = function() {
  alert(1);
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


goog.exportSymbol('lost_tracker.app', lost_tracker.app);
goog.exportSymbol('lost_tracker.app.advanceState',
    lost_tracker.app.advanceState);
