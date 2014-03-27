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
 * 
 * @param {object} source TODO: doc
 * @param {object} key TODO: doc
 * @param {object} datum TODO: doc
 * @param {object} newValue TODO: doc
 * @param {object} oldValue TODO: doc
 */
lost_tracker.Tabulator.prototype.updateCell = function(source, key, datum, newValue, oldValue) {
  var self = this;
  if (newValue == oldValue) {
    lost_tracker.Tabulator.LOG.fine('No update needed (oldValue=newValue)');
    return;
  }
  lost_tracker.Tabulator.LOG.fine('Setting ' + datum + ' on item ' + key + ' to ' + newValue);
  var url = '/cell/' + this.table.getAttribute('data-name') + '/' + key + '/' + datum;
  goog.net.XhrIo.send(url, function(evt) {
    var xhr = evt.target;
    var response = xhr.getResponseJson();
    if (xhr.isSuccess()) {
      lost_tracker.Tabulator.LOG.fine('Successfully updated the cell');
      source.setAttribute('data-current-value', response.new_value);
    } else {
      lost_tracker.Tabulator.LOG.warning('Error updating the cell!');
      var resolvedValue = self.resolveConflict(newValue, oldValue, response['db_value']);
      self.updateCell(source, key, datum, resolvedValue, response['db_value']);
      // TODO: show error
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
lost_tracker.Tabulator.prototype.resolveConflict = function(newValue, oldValue, serverValue) {
  var dialog1 = new goog.ui.Dialog();
  dialog1.setContent(
    'Your Value: ' + newValue + '<br />' +
    'Old Value: ' + oldValue + '<br />' +
    'Server Value: ' + serverValue
  );
  dialog1.setTitle('Data Conflict');
  dialog1.setButtonSet(goog.ui.Dialog.ButtonSet.OK_CANCEL);
  dialog1.setVisible(true);
  goog.events.listen(dialog1, goog.ui.Dialog.EventType.SELECT, function(e) {
    if (e.key == 'cancel') {
      return null;
    } else {
      var celem = dialog1.getContentElement();
      return selectedValue;
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
