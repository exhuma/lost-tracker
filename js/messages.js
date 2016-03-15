goog.provide('lost_tracker.MessageView');

goog.require('goog.array');
goog.require('goog.dom');
goog.require('goog.dom.classes');
goog.require('goog.dom.forms');
goog.require('goog.events');
goog.require('goog.fx.dom');
goog.require('goog.net.XhrIo');
goog.require('goog.ui.Dialog');


/**
 * Creates a new MessageView.
 *
 * @constructor
 */
lost_tracker.MessageView = function() {
  this.init();
};


lost_tracker.MessageView.prototype.init = function() {
  var self = this;
  var actionMap = {
    'delete': self.on_delete_click
  };

  var messageButtons = goog.dom.getElementsByClass('message-button');
  goog.array.forEach(messageButtons, function(button) {
    var action = button.getAttribute('data-action');
    var fun = actionMap[action];
    goog.events.listen(button, goog.events.EventType.CLICK, fun,
        false, self);
  });
};


/**
 * EventHandler for the delete button
 */
lost_tracker.MessageView.prototype.on_delete_click = function(evt) {
  var self = this;
  var confirmationDialog = new goog.ui.Dialog();
  var container = goog.dom.getAncestorByTagNameAndClass(evt.target, 'div');
  var span = goog.dom.getAncestorByTagNameAndClass(evt.target, 'span');
  var messageId = container.getAttribute('data-message-id');
  confirmationDialog.setContent(
    'Sind Sie sicher dass sie die Zeile #' + messageId + ' l&ouml;schen wollen?'
  );
  confirmationDialog.setTitle('Sind Sie sicher?');
  confirmationDialog.setButtonSet(goog.ui.Dialog.ButtonSet.YES_NO);
  confirmationDialog.setVisible(true);
  goog.events.listen(confirmationDialog, goog.ui.Dialog.EventType.SELECT, function(e) {
    if (e.key == 'yes') {
      self.deleteMessage(container, messageId);
    }
  });

};


lost_tracker.MessageView.prototype.deleteMessage = function(container, messageId) {
  var messageURL = $COMMENT_PREFIX + '/' + messageId;
  goog.net.XhrIo.send(messageURL, function(evt) {
    var xhr = evt.target;
    if (xhr.isSuccess()) {
      var anim = new goog.fx.dom.FadeOutAndHide(container, 300);
      anim.play();
    } else {
      var alertDialog = new goog.ui.Dialog();
      alertDialog.setContent('Fehlgeschlagen!');
      alertDialog.setTitle('Fehler');
      alertDialog.setButtonSet(goog.ui.Dialog.ButtonSet.OK);
      alertDialog.setVisible(true);
    }
  }, 'DELETE');
};

// vim: set ft=closure.javascript :
