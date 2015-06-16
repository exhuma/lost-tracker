goog.provide('lost_tracker.Tabulator');

goog.require('goog.array');
goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.events.EventType');
goog.require('goog.json');
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
lost_tracker.Tabulator.prototype.updateCell = function(source, key, datum, newValue, oldValue, this_obj) {
  lost_tracker.Tabulator.LOG.fine('Setting ' + datum + ' on item ' + key +
      ' from ' + oldValue +
      ' to ' + newValue);
  if (newValue == oldValue) {
    lost_tracker.Tabulator.LOG.fine('No update needed (oldValue=newValue)');
    this_obj.setCellValue(source, newValue);
    return;
  }
  var url = $TABULAR_PREFIX + '/cell/' + this_obj.table.getAttribute('data-name') + '/' + key + '/' + datum;
  goog.net.XhrIo.send(url, function(evt) {
    var xhr = evt.target;
    var response = xhr.getResponseJson();
    if (xhr.isSuccess()) {
      lost_tracker.Tabulator.LOG.fine('Successfully updated the cell');
      this_obj.setCellValue(source, response.new_value);
    } else {
      lost_tracker.Tabulator.LOG.warning('Error updating the cell!');
      // Ask the user for a fixed value and run updateCell recursively again.
      this_obj.resolveConflict(newValue, oldValue, response['db_value'], source, key, datum);
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
        self.updateCell(source, key, datum, selectedValue, serverValue, self);
      } else {
        lost_tracker.Tabulator.LOG.severe('No value received for conflict resolution.');
      }
    } else {
      lost_tracker.Tabulator.LOG.shout('Unsupported dialog action: ' + e.key + '!');
    }
  });
};


/**
 * Writes data into an object which will only be sent to the remote server if
 * the user clicks a "save" button.
 * @param {object}  TODO: doc
 */
lost_tracker.Tabulator.prototype.prepareCellForCreation = function(source, key, datum, newValue, oldValue, this_obj) {
  var row = goog.dom.getAncestorByTagNameAndClass(source, 'TR');
  var preparedEntity = row.getAttribute('data-values');
  if (goog.isNull(preparedEntity)) {
    preparedEntity = {};
  } else {
    preparedEntity = goog.json.parse(preparedEntity);
  }
  preparedEntity[datum] = newValue;
  row.setAttribute('data-values', goog.json.serialize(preparedEntity));
};

/**
 * 
 * @param {object} element TODO: doc
 */
lost_tracker.Tabulator.prototype.attachCellEvents = function(element, hasDbEntity) {
  var row = goog.dom.getAncestorByTagNameAndClass(element, 'TR');
  var self = this;
  var actionFunc;

  if (hasDbEntity) {
    actionFunc = self.updateCell;
  } else {
    actionFunc = self.prepareCellForCreation;
  }
  goog.events.listen(element, goog.events.EventType.BLUR, function(evt) {
    actionFunc(
      element,
      row.id,
      element.getAttribute('data-cell-name'),
      goog.dom.getTextContent(evt.target),
      element.getAttribute('data-current-value'),
      self);
  });
};


/**
 * 
 * @param {object} element TODO: doc
 */
lost_tracker.Tabulator.prototype.attachCheckEvents = function(element, hasDbEntity) {
  var row = goog.dom.getAncestorByTagNameAndClass(element, 'TR');
  var self = this;
  var actionFunc;

  if (hasDbEntity) {
    actionFunc = self.updateCell;
  } else {
    actionFunc = self.prepareCellForCreation;
  }

  goog.events.listen(element, goog.events.EventType.CHANGE, function(evt) {
    actionFunc(
      element,
      row.id,
      element.getAttribute('data-cell-name'),
      evt.target.checked,
      element.getAttribute('data-current-value').toLowerCase() == 'true',
      self);
  });
};


/**
 * Displays an error dialog
 * 
 * @param {string} message The message shown to the user.
 */
lost_tracker.Tabulator.prototype.showError= function(message) {
  var confirmationDialog = new goog.ui.Dialog();
  confirmationDialog.setContent(message);
  confirmationDialog.setTitle('Es trat ein Fehler auf dem Server auf!');
  confirmationDialog.setButtonSet(goog.ui.Dialog.ButtonSet.OK);
  confirmationDialog.setVisible(true);
};


/**
 * Delete a row containing a given cell.
 * 
 * @param {node} node: The HTML node contained in the row.
 */
lost_tracker.Tabulator.prototype.deleteRow = function(node) {
  var self = this;
  var loaderUrl = '/static/icons/loading.gif';
  var defaultImage = node.src;
  var row = goog.dom.getAncestorByTagNameAndClass(node, 'TR');
  var table = goog.dom.getAncestorByTagNameAndClass(node, 'TABLE');
  var id = row.getAttribute('id');
  var table = table.getAttribute('data-name');
  node.src = loaderUrl;
  var confirmationDialog = new goog.ui.Dialog();
  confirmationDialog.setContent(
    'Sind Sie sicher dass sie die Zeile ' + id + ' l&ouml;schen wollen?'
  );
  confirmationDialog.setTitle('Sind Sie sicher?');
  confirmationDialog.setButtonSet(goog.ui.Dialog.ButtonSet.YES_NO);
  confirmationDialog.setVisible(true);
  goog.events.listen(confirmationDialog, goog.ui.Dialog.EventType.SELECT, function(e) {
    if (e.key == 'yes') {
      var url = $TABULAR_PREFIX + '/' + table + '/' + id;
      goog.net.XhrIo.send(url, function(evt) {
        var xhr = evt.target;
        if (xhr.isSuccess()) {
          goog.dom.removeNode(row);
        } else {
          self.showError('Dies kann auftreten wenn die Datenbank aus Sicherheitsgr&uuml;nden das L&ouml;schen verhindert!');
        }
      }, 'DELETE');
    }
    node.src = defaultImage;;
  });
};


/**
 * Creates a new row in the DB.
 * 
 * @param {node} node: The HTML node contained in the row.
 */
lost_tracker.Tabulator.prototype.saveNewRow = function(node) {
  var self = this;
  var loaderUrl = '/static/icons/loading.gif';
  var defaultImage = node.src;
  var row = goog.dom.getAncestorByTagNameAndClass(node, 'TR');
  var table = goog.dom.getAncestorByTagNameAndClass(node, 'TABLE');
  var data = row.getAttribute('data-values');
  var table = table.getAttribute('data-name');
  var url = $TABULAR_PREFIX + '/' + table;
  node.src = loaderUrl;
  goog.net.XhrIo.send(url, function(evt) {
    var xhr = evt.target;
    if (xhr.isSuccess()) {
      row.setAttribute('data-values', '{}');
      var cells = goog.dom.getElementsByTagNameAndClass('TD', 'tabularcell', row);
      goog.array.forEach(cells, function(cell) {
        goog.dom.setTextContent(cell, '');
        window.location.reload();
      });
    } else {
      self.showError('Daten wurden nicht gespeichert :(');
    }
    node.src = defaultImage;;
  }, 'POST', data, {'Content-Type': 'application/json'});
};


/**
 * 
 * @param {object}  TODO: doc
 */
lost_tracker.Tabulator.prototype.decorate = function() {
  var self = this;
  var elems = goog.dom.getElementsByClass('delete_icon');
  goog.array.forEach(elems, function(elmnt) {
    goog.events.listen(elmnt, goog.events.EventType.CLICK, function(evt) {
      self.deleteRow(elmnt);
    });
  });

  var saveIcon = goog.dom.getElementsByClass('save_icon')[0];
  goog.events.listen(saveIcon, goog.events.EventType.CLICK, function(evt) {
    self.saveNewRow(saveIcon);
  });

  var body = goog.dom.getElementsByTagNameAndClass('TBODY', undefined, this.table)[0];
  var elems = goog.dom.getElementsByClass('tabularcell', body);
  goog.array.forEach(elems, function(elmnt) {
    if (elmnt.tagName == 'TD') {
      elmnt.contentEditable = 'true';
      self.attachCellEvents(elmnt, true);
    } else if (elmnt.tagName == 'INPUT' && elmnt.type == 'checkbox') {
      self.attachCheckEvents(elmnt, true);
    }
  });

  var foot = goog.dom.getElementsByTagNameAndClass('TFOOT', undefined, this.table)[0];
  var elems = goog.dom.getElementsByClass('tabularcell', foot);
  goog.array.forEach(elems, function(elmnt) {
    if (elmnt.tagName == 'TD') {
      elmnt.contentEditable = 'true';
      self.attachCellEvents(elmnt, false);
    } else if (elmnt.tagName == 'INPUT' && elmnt.type == 'checkbox') {
      self.attachCheckEvents(elmnt, false);
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
