import logging

from envelopes import Envelope
from jinja2 import Environment, PackageLoader

_ENV = Environment(loader=PackageLoader('lost_tracker', 'templates'))
LOG = logging.getLogger(__name__)


def send(template, to, data):
    if template == 'registration_check':
        subject = u'Please check and confirm this registration.'
    elif template == 'confirm':
        subject = u'Confirmation of your registration'
    elif template == 'registration_update':
        subject = u'Lost Registration Change'
    elif template == 'welcome':
        subject = u'Welcome to Lost, your registration is completed.'
    else:
        raise ValueError('Unsupported e-mail template: {}'.format(template))

    tmpl = _ENV.get_template('email/{}.txt'.format(template))
    content = tmpl.render(**data)
    mail = Envelope(
        from_addr=(u'no_reply@lost.lu', u'lost.lu registration'),
        to_addr=to,
        subject=subject,
        text_body=content)
    LOG.debug('Sending email out to {!r} via localhost'.format(to))
    mail.send('localhost')
