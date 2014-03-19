goog.provide('lost_tracker.SlotEditor');

goog.require('goog.array');
goog.require('goog.debug.Logger');
goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.json');
goog.require('goog.net.XhrIo');
goog.require('goog.string');
goog.require('goog.ui.AdvancedTooltip');
goog.require('goog.ui.PopupBase.EventType');


/**
 * The class logger
 */
lost_tracker.SlotEditor.LOG = goog.debug.Logger.getLogger(
  'lost_tracker.SlotEditor');


/**
 * Creates a new SlotEditor.
 *
 * @param {string} slotsTableId The SGML ID of the table which contains the
 *     time-slots.
 * @param {string} noSlotsTableId The ID of the table containing unassigned
 *     groups.
 * @constructor
 */
lost_tracker.SlotEditor = function(slotsTableId, noSlotsTableId) {
  this.slotsTable = goog.dom.getElement(slotsTableId);
  this.noSlotsTable = goog.dom.getElement(noSlotsTableId);
  this.init();
};


/**
 * Updates a tooltip with the HTML content from a remote call.
 *
 * @param {string} group_name The name of the group. This name is used to
 *     look-up the data on the remote-server.
 * @param {goog.ui.AdvancedTooltip} tooltip The tooltip which is going to be
 *     updated.
 */
lost_tracker.SlotEditor.prototype.updateTooltip = function(
    groupName, tooltip) {
  tooltip.setHtml('Loading... <img valign="middle" ' +
                  'src="/static/images/ajax-loader.gif" />');
  var url = '/js-fragment/group-tooltip/' + groupName;
  goog.net.XhrIo.send(url, function(evt) {
    var xhr = evt.target;
    if (xhr.isSuccess()) {
      tooltip.setHtml(xhr.getResponseText());
    } else {
      tooltip.setHtml('Server error!');
    }
  });
};


/**
 * Callback which is executed when the text of a slot changed.
 *
 * @param {string} groupName The name of the group (the new value of the cell).
 * @param {string} time {object} The start-time (time-slot) as HH:MM.
 * @param {string} oldValue {object} The value of the cell *before* the change
 *     (the group-name which was in the cell before the change, or empty).
 */
lost_tracker.SlotEditor.prototype.slotTextChanged = function(node, groupName,
    time, oldValue) {
  var empty = goog.string.isEmptySafe;
  var self = this;
  var url;
  var newValue;
  var callback;

  if (empty(groupName) && !empty(oldValue)) {
    url = '/group/' + oldValue + '/timeslot';
    newValue = null;
    callback = function(response) {
        var reserveNode = self.addReserve(oldValue);
        node.setAttribute('data-group_id', '');
        reserveNode.setAttribute('data-group_id', response.group_id);
    };
  } else if (!empty(groupName)) {
    url = '/group/' + groupName + '/timeslot';
    newValue = time;
    callback = function(response) {
        node.setAttribute('data-group_id', response.group_id);
        self.removeReserve(groupName);
    };
  } else {
    lost_tracker.SlotEditor.LOG.fine('Unexpected input! new_value: ' +
        groupName + ' oldValue: ' + oldValue);
    return;
  }

  goog.net.XhrIo.send(url, function(evt) {
    var xhr = evt.target;
    if (xhr.isSuccess()) {
      var response = xhr.getResponseJson();
      callback(response);
    } else {
      // TODO: show error
      lost_tracker.SlotEditor.LOG.severe('XHR failed!');
    }
  }, 'PUT', goog.json.serialize({"new_slot": newValue}),
  {'Content-Type': 'application/json'});

};


/**
 * Adds the group to the "reserve" table (unassigned groups).
 *
 * @param {sring} groupName The group name.
 */
lost_tracker.SlotEditor.prototype.addReserve = function(groupName) {
  lost_tracker.SlotEditor.LOG.fine('Putting ' + groupName + ' on reserve');
  var self = this;
  var header = goog.dom.getFirstElementChild(this.noSlotsTable);
  var body = goog.dom.getNextElementSibling(header);
  var rows = goog.dom.getElementsByTagNameAndClass('tr', null, body);
  var newCell = goog.dom.createDom('td', null, groupName);
  this.attachToolTip(newCell);
  var newRow = goog.dom.createDom('tr', null, newCell)
  var inserted = goog.array.some(rows, function(row) {
    var cols = goog.dom.getElementsByTagNameAndClass('td', null, row);
    var cellName = goog.dom.getTextContent(cols[0]);
    if (cellName == groupName) {
      lost_tracker.SlotEditor.LOG.severe(groupName +
        ' already exists in reserve table!');
    } else if (groupName < cellName) {
      lost_tracker.SlotEditor.LOG.info('Inserting ' +
        groupName + ' before ' + row);
      body.insertBefore(newRow, row);
      return true;
    }
  });
  if (!inserted) {
    lost_tracker.SlotEditor.LOG.info('Not inserted. Appending now!');
    body.appendChild(newRow);
  }
  return newCell;
};


/**
 * Removes the group from the "reserve" table (unassigned groups).
 *
 * @param {sring} groupName The group name.
 */
lost_tracker.SlotEditor.prototype.removeReserve = function(groupName) {
  lost_tracker.SlotEditor.LOG.fine('Removing "' + groupName +
      '" from reserve');
  var self = this;
  var header = goog.dom.getFirstElementChild(this.noSlotsTable);
  var body = goog.dom.getNextElementSibling(header);
  var rows = goog.dom.getElementsByTagNameAndClass('tr', null, body);
  goog.array.some(rows, function(row) {
    var cols = goog.dom.getElementsByTagNameAndClass('td', null, row);
    var cellName = goog.dom.getTextContent(cols[0]);
    if (cellName == groupName) {
      goog.dom.removeNode(row);
      return true;
    }
  });
};


/**
 * Attaches a tooltip to a HTML node. The tooltip contains additional data for
 * groups. The node must contain the data attribite `data-group_id` containing
 * the ID of the group.
 *
 * @param {Node} node The node to which the tooltip should be attached.
 */
lost_tracker.SlotEditor.prototype.attachToolTip = function(node) {
  var self = this;
  var tooltip = new goog.ui.AdvancedTooltip(node);
  goog.events.listen(tooltip, goog.ui.PopupBase.EventType.BEFORE_SHOW,
      function(evt) {
    var groupId = node.getAttribute('data-group_id');
    if (goog.string.isEmptySafe(groupId)) {
      return false;
    }
    self.updateTooltip(groupId, tooltip);
  });
  tooltip.className = 'tooltip';
  tooltip.setHotSpotPadding(new goog.math.Box(5, 5, 5, 5));
  tooltip.setCursorTracking(true);
  tooltip.setMargin(new goog.math.Box(0, 0, 0, 0));
  tooltip.setHideDelayMs(250);
};


/**
 * Initialises the slot editor.
 */
lost_tracker.SlotEditor.prototype.init = function() {
  var nodeText = goog.dom.getTextContent;
  var trim = goog.string.trim;
  var self = this;
  var header = goog.dom.getFirstElementChild(this.slotsTable);
  var body = goog.dom.getNextElementSibling(header);
  var rows = goog.dom.getElementsByTagNameAndClass('tr', null, body);
  goog.array.forEach(rows, function(element) {
    var cols = goog.dom.getElementsByTagNameAndClass('td', null, element);
    var timeSlot = cols[0];
    var dirA = cols[1];
    var dirB = cols[2];
    var oldValueA = trim(nodeText(dirA));
    var oldValueB = trim(nodeText(dirB));
    self.attachToolTip(dirA);
    self.attachToolTip(dirB);
    goog.events.listen(dirA, goog.events.EventType.BLUR, function(evt) {
      self.slotTextChanged(dirA,
                           trim(nodeText(evt.target)),
                           trim(nodeText(timeSlot)),
                           oldValueA);
      oldValueA = trim(nodeText(evt.target));
    });
    goog.events.listen(dirB, goog.events.EventType.BLUR, function(evt) {
      self.slotTextChanged(dirB,
                           trim(nodeText(evt.target)),
                           trim(nodeText(timeSlot)),
                           oldValueB);
      oldValueB = trim(nodeText(evt.target));
    });
  });

  var nsHeader = goog.dom.getFirstElementChild(this.noSlotsTable);
  var nsBody = goog.dom.getNextElementSibling(nsHeader);
  var nsRows = goog.dom.getElementsByTagNameAndClass('tr', null, nsBody);
  goog.array.forEach(nsRows, function(element) {
    var cols = goog.dom.getElementsByTagNameAndClass('td', null, element);
    self.attachToolTip(cols[0]);
  });
};


// vim: set ft=closure.javascript :
