#!/usr/bin/env python
activate_this = '/path/to/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import os
os.environ['LOST_TRACKER_SETTINGS'] = '/path/to/siteconf.py'

from lost_tracker.main import app as application  # NOQA
# vim: set ft=python :
