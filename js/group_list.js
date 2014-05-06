goog.provide('lost_tracker.GroupList');

goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.net.XhrIo');
goog.require('goog.string');
goog.require('goog.ui.AdvancedTooltip');
goog.require('goog.ui.PopupBase.EventType');


/**
 * Creates a new GroupList.
 *
 * @param {string} tableId The SGML ID of the table which contains the
 *     time-slots.
 * @constructor
 */
lost_tracker.GroupList = function(tableId) {
  this.list_ = goog.dom.getElement(tableId);
  this.init();
};


/**
 * Updates a tooltip with the HTML content from a remote call.
 *
 * @param {string} groupName The name of the group. This name is used to
 *     look-up the data on the remote-server.
 * @param {goog.ui.AdvancedTooltip} tooltip The tooltip which is going to be
 *     updated.
 */
lost_tracker.GroupList.prototype.updateTooltip = function(
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
 * Attaches a tooltip to a HTML node. The tooltip contains additional data for
 * groups. The node must contain the data attribite `data-group_id` containing
 * the ID of the group.
 *
 * @param {Element} node The node to which the tooltip should be attached.
 */
lost_tracker.GroupList.prototype.attachToolTip = function(node) {
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


lost_tracker.GroupList.prototype.init = function() {
  var self = this;
  var nodeText = goog.dom.getTextContent;
  var trim = goog.string.trim;
  var header = goog.dom.getFirstElementChild(this.list_);
  var body = goog.dom.getNextElementSibling(header);
  var rows = goog.dom.getElementsByTagNameAndClass('tr', null, body);
  goog.array.forEach(rows, function(element) {
    var cols = goog.dom.getElementsByTagNameAndClass('td', null, element);
    var groupCell = cols[0];
    var groupName = trim(nodeText(groupCell));
    self.attachToolTip(groupCell);
  });
};

// vim: set ft=closure.javascript :
