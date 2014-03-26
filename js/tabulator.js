goog.provide('lost_tracker.Tabulator');

goog.require('goog.array');
goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.events.EventType');
goog.require('goog.log');


/**
 * 
 * @param {object} element TODO: doc
 * @constructor
 */
lost_tracker.Tabulator = function(element) {
  this.table = goog.dom.getElement(element);
  this.init();
};

/**
 * 
 * @param {object} element TODO: doc
 */
lost_tracker.Tabulator.prototype.attachCellEvents = function(element) {
  // TODO: implement
};


/**
 * 
 * @param {object} source TODO: doc
 * @param {object} key TODO: doc
 * @param {object} datum TODO: doc
 * @param {object} newValue TODO: doc
 * @param {object} oldValue TODO: doc
 * @param {object} revert TODO: doc
 */
lost_tracker.Tabulator.prototype.updateCell = function(source, key, datum, newValue, oldValue, revert) {
  lost_tracker.Tabulator.LOG.fine('Setting ' + datum + ' on item ' + key + ' to ' + newValue);
  var url = '/cell/' + this.table.getAttribute('data-name') + '/' + key + '/' + datum;
  goog.net.XhrIo.send(url, function(evt) {
    var xhr = evt.target;
    if (xhr.isSuccess()) {
      lost_tracker.Tabulator.LOG.fine('Successfully updated the cell');
      var response = xhr.getResponseJson();
      source.setAttribute('data-current-value', (response.new_value ? 'true' : 'false'));
    } else {
      lost_tracker.Tabulator.LOG.warning('Error updating the cell!');
      revert(oldValue);
      // TODO: show error
    }
  }, 'PUT', goog.json.serialize({
    'newValue': newValue,
    'oldValue': oldValue
  }), {'Content-Type': 'application/json'});
};


/**
 * 
 * @param {object} element TODO: doc
 */
lost_tracker.Tabulator.prototype.attachCheckEvents = function(element) {
  var row = goog.dom.getAncestorByTagNameAndClass(element, 'TR');
  var self = this;

  goog.events.listen(element, goog.events.EventType.CHANGE, function(evt) {
    self.updateCell(
      element,
      row.id,
      element.getAttribute('data-cell-name'),
      evt.target.checked,
      element.getAttribute('data-current-value').toLowerCase() == 'true',
      function(oldval) {
        element.checked = oldval;
      });
  });
};


/**
 * 
 * @param {object}  TODO: doc
 */
lost_tracker.Tabulator.prototype.decorate = function() {
  var self = this;
  var elems = goog.dom.getElementsByClass('tabularcell');
  goog.array.forEach(elems, function(elmnt) {
    if (elmnt.tagName == 'TD') {
      elmnt.contentEditable = 'true';
      self.attachCellEvents(elmnt);
    } else if (elmnt.tagName == 'INPUT' && elmnt.type == 'checkbox') {
      self.attachCheckEvents(elmnt);
    }
  });
};


/**
 * 
 * @param {object}  TODO: doc
 */
lost_tracker.Tabulator.prototype.init = function() {
  this.decorate();
};


/**
 * The class logger
 */
lost_tracker.Tabulator.LOG = goog.log.getLogger(
  'lost_tracker.Tabulator');
// vim: set ft=closure.javascript :
