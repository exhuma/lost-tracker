goog.provide('lost_tracker.RegistrationForm');

goog.require('goog.dom');


/**
 * 
 * @param form_id {object} TODO: doc
 * @constructor
 */
lost_tracker.RegistrationForm = function(form_id) {
  var elem = goog.dom.getElement(form_id);
  window['console']['log'](elem);
};


// vim: set ft=closure.javascript :
