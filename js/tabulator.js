goog.provide('lost_tracker.Tabulator');

goog.require('goog.array');
goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.events.EventType');
goog.require('goog.log');
goog.require('goog.ui.Dialog');


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
 * Sets the "committed" value of a cell (data attribute and text).
 * @param {object} setCellValue TODO: doc
 */
lost_tracker.Tabulator.prototype.setCellValue = function(element, value) {
  lost_tracker.Tabulator.LOG.fine('Commiting value ' + value + ' to ' + element);
  element.setAttribute('data-current-value', value);
  goog.dom.setTextContent(element, value);
};


/**
 * 
 * @param {object} source TODO: doc
 * @param {object} key TODO: doc
 * @param {object} datum TODO: doc
 * @param {object} newValue TODO: doc
 * @param {object} oldValue TODO: doc
 */
lost_tracker.Tabulator.prototype.updateCell = function(source, key, datum, newValue, oldValue) {
  lost_tracker.Tabulator.LOG.fine('Setting ' + datum + ' on item ' + key +
      ' from ' + oldValue +
      ' to ' + newValue);
  var self = this;
  if (newValue == oldValue) {
    lost_tracker.Tabulator.LOG.fine('No update needed (oldValue=newValue)');
    self.setCellValue(source, newValue);
    return;
  }
  var url = '/cell/' + this.table.getAttribute('data-name') + '/' + key + '/' + datum;
  goog.net.XhrIo.send(url, function(evt) {
    var xhr = evt.target;
    var response = xhr.getResponseJson();
    if (xhr.isSuccess()) {
      lost_tracker.Tabulator.LOG.fine('Successfully updated the cell');
      self.setCellValue(source, response.new_value);
    } else {
      lost_tracker.Tabulator.LOG.warning('Error updating the cell!');
      // Ask the user for a fixed value and run updateCell recursively again.
      self.resolveConflict(newValue, oldValue, response['db_value'], source, key, datum);
    }
  }, 'PUT', goog.json.serialize({
    'newValue': newValue,
    'oldValue': oldValue
  }), {'Content-Type': 'application/json'});
};


/**
 * 
 * @param {object} newValue TODO: doc
 * @param {object} oldValue TODO: doc
 * @param {object} serverValue TODO: doc
 */
lost_tracker.Tabulator.prototype.resolveConflict = function(newValue, oldValue, serverValue,
    source, key, datum) {
  var self = this;
  var dialog1 = new goog.ui.Dialog();
  dialog1.setContent(
    'Seit dem letzten Seitenaufruf wurden die Daten auf dem Server ver&auml;ndert! ' +
    'Bitte w&auml;hlen Sie einen der folgenden Werte aus, welcher gespeichert werden soll:<br /><br />' +
    '<input type="radio" name="selected-value" value="' + newValue + '" checked /><strong>Ihr eben eingegebener Wert:</strong> ' + newValue + '<br />' +
    '<input type="radio" name="selected-value" value="' + oldValue + '" /><strong>Vorheriger Wert vom Server:</strong> ' + oldValue + '<br />' +
    '<input type="radio" name="selected-value" value="' + serverValue + '" /><strong>Jetziger Wert auf dem Server:</strong> ' + serverValue
  );
  dialog1.setTitle('Datenkonflikt');
  dialog1.setButtonSet(goog.ui.Dialog.ButtonSet.OK);
  dialog1.setVisible(true);
  goog.events.listen(dialog1, goog.ui.Dialog.EventType.SELECT, function(e) {
    if (e.key == 'ok') {
      var celem = dialog1.getContentElement();
      var inputs = goog.dom.getElementsByTagNameAndClass('INPUT', undefined, celem);
      var selectedValue = null;
      goog.array.some(inputs, function(element) {
        if (element.checked) {
          selectedValue = element.value;
          return true;
        }
      });
      if (!goog.string.isEmptySafe(selectedValue)) {
        self.updateCell(source, key, datum, selectedValue, serverValue);
      } else {
        lost_tracker.Tabulator.LOG.severe('No value received for conflict resolution.');
      }
    } else {
      lost_tracker.Tabulator.LOG.shout('Unsupported dialog action: ' + e.key + '!');
    }
  });
};

/**
 * 
 * @param {object} element TODO: doc
 */
lost_tracker.Tabulator.prototype.attachCellEvents = function(element) {
  var row = goog.dom.getAncestorByTagNameAndClass(element, 'TR');
  var self = this;

  goog.events.listen(element, goog.events.EventType.BLUR, function(evt) {
    self.updateCell(
      element,
      row.id,
      element.getAttribute('data-cell-name'),
      goog.dom.getTextContent(evt.target),
      element.getAttribute('data-current-value'));
  });
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
      element.getAttribute('data-current-value').toLowerCase() == 'true');
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
