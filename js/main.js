goog.require('goog.debug.Console');
goog.require('goog.log');
goog.require('lost_tracker.GroupList');
goog.require('lost_tracker.Profile');
goog.require('lost_tracker.RegistrationForm');
goog.require('lost_tracker.SlotEditor');
goog.require('lost_tracker.Tabulator');
goog.require('lost_tracker.app');

goog.exportSymbol('lost_tracker.app.attachEvents',
    lost_tracker.app.attachEvents);

goog.exportSymbol('lost_tracker.app.drawSums',
    lost_tracker.app.drawSums);

goog.exportSymbol('lost_tracker.RegistrationForm',
    lost_tracker.RegistrationForm);

goog.exportSymbol('lost_tracker.SlotEditor',
  lost_tracker.SlotEditor);

goog.exportSymbol('lost_tracker.Tabulator',
  lost_tracker.Tabulator);

goog.exportSymbol('lost_tracker.GroupList',
  lost_tracker.GroupList);


goog.exportSymbol('lost_tracker.Profile',
  lost_tracker.Profile);


if (goog.DEBUG) {
  var debugConsole = new goog.debug.Console;
  debugConsole.setCapturing(true);
  var logger = goog.log.getLogger('lost_tracker');
  logger.setLevel(goog.log.Level.ALL);
}

// vim: set ft=closure.javascript :
