goog.provide('lost_tracker.Tabulator');

goog.require('goog.dom');


/**
 * 
 * @param {object} element TODO: doc
 * @constructor
 */
lost_tracker.Tabulator = function(element) {
  this.table = goog.dom.getElement(element);
};
// vim: set ft=closure.javascript :
