goog.provide('lost_tracker.Profile');

goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.net.XhrIo');


/**
 * Creates a new Profile.
 *
 * @constructor
 */
lost_tracker.Profile = function() {
  this.button = goog.dom.getElement('disconnect-button');
  this.init();
};


lost_tracker.Profile.prototype.init = function() {
  var self = this;

  goog.events.listen(self.button, goog.events.EventType.CLICK, function(evt) {
    var url = '/connect/twitter/15689631';
    goog.net.XhrIo.send(url, function(evt) {
      var xhr = evt.target;
      if (xhr.isSuccess()) {
        window['console']['log']('Removed');  // TODO: DEBUG LOG!!
      } else {
        window['console']['log']('error');  // TODO: DEBUG LOG!!
      }
    }, 'DELETE');
  });
};

// vim: set ft=closure.javascript :
