#!/usr/bin/env python
activate_this = '/path/to/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import logging
logging.basicConfig(level=logging.WARNING,
                    filename='/var/www/lost.lu/www/applog/error_log')

from lost_tracker.main import app as application  # NOQA
# vim: set ft=python :
