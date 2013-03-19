goog.provide('lost_tracker.model.Station');
goog.provide('lost_tracker.model.Group');


/**
 * @constructor
 */
lost_tracker.model.Station = function(name) {
  this.name = name;
  this.order = 0;
};


lost_tracker.model.Station.prototype.toString = function() {
  return '<Station ' + this.name + '>';
};


lost_tracker.model.Station.all = function() {
  return [
    new lost_tracker.model.Station('station 1'),
    new lost_tracker.model.Station('station 2'),
    new lost_tracker.model.Station('station 3'),
    new lost_tracker.model.Station('station 4'),
    new lost_tracker.model.Station('station 5'),
    new lost_tracker.model.Station('station 6')
  ];
};
