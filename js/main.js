goog.require('goog.debug.Console');
goog.require('lost_tracker.RegistrationForm');
goog.require('lost_tracker.SlotEditor');
goog.require('lost_tracker.app');

goog.exportSymbol('lost_tracker.app.attachEvents',
    lost_tracker.app.attachEvents);

goog.exportSymbol('lost_tracker.app.drawSums',
    lost_tracker.app.drawSums);

goog.exportSymbol('lost_tracker.RegistrationForm',
    lost_tracker.RegistrationForm);

goog.exportSymbol('lost_tracker.SlotEditor',
  lost_tracker.SlotEditor);


if (goog.DEBUG) {
  var debugConsole = new goog.debug.Console;
  debugConsole.setCapturing(true);
  var logger = goog.debug.Logger.getLogger('lost_tracker');
  logger.setLevel(goog.debug.Logger.Level.ALL);
}

// vim: set ft=closure.javascript :
