goog.provide('lost_tracker.SocialPage');

goog.require('goog.array');
goog.require('goog.dom');
goog.require('goog.dom.classes');
goog.require('goog.dom.forms');
goog.require('goog.events');
goog.require('goog.net.XhrIo');
goog.require('goog.ui.Dialog');


/**
 * Creates a new SocialPage.
 *
 * @constructor
 */
lost_tracker.SocialPage = function() {
  this.init();
};


lost_tracker.SocialPage.prototype.init = function() {
  var self = this;

  var loginButtons = goog.dom.getElementsByClass('login-button');
  goog.array.forEach(loginButtons, function(element) {
    goog.events.listen(element, goog.events.EventType.CLICK, function(evt) {
      var form = goog.dom.getAncestorByTagNameAndClass(evt.target, 'form');
      form.submit();
    });
  });

  var connectButtons = goog.dom.getElementsByClass('social-connect-button');
  goog.array.forEach(connectButtons, function(element) {
    goog.events.listen(element, goog.events.EventType.CLICK, function(evt) {
      var form = goog.dom.getAncestorByTagNameAndClass(evt.target, 'form');
      form.submit();
    });
  });

  var disconnectButtons = goog.dom.getElementsByClass('social-disconnect-button');
  goog.array.forEach(disconnectButtons, function(element) {
    goog.events.listen(element, goog.events.EventType.CLICK, function(evt) {
      var span = goog.dom.getAncestorByTagNameAndClass(evt.target, 'span');
      var providerId = span.getAttribute('data-provider-id');
      var userId = span.getAttribute('data-user-id');
      var connectionURL = '/connect/' + providerId + '/' + userId;
      goog.net.XhrIo.send(connectionURL, function(evt) {
        var xhr = evt.target;
        if (xhr.isSuccess()) {
          window.location.reload(true);
        } else {
          var alertDialog = new goog.ui.Dialog();
          alertDialog.setContent('Verbindungstrennung fehlgeschlagen.');
          alertDialog.setTitle('Fehler');
          alertDialog.setButtonSet(goog.ui.Dialog.ButtonSet.OK);
          alertDialog.setVisible(true);
        }
      }, 'DELETE');
    });
  });

};

// vim: set ft=closure.javascript :
