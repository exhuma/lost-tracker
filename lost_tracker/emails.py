import logging

from envelopes import Envelope
from jinja2 import Environment, PackageLoader

_ENV = Environment(loader=PackageLoader('lost_tracker', 'templates'))
LOG = logging.getLogger(__name__)


def send(template, to, data):
    if template == 'registration_check':
        subject = u'New registration for {0.name}'.format(data['group'])
    elif template == 'confirm':
        subject = u'Please confirm your registration for lost.lu'
    elif template == 'registration_update':
        subject = u'Lost Registration Change'
    elif template == 'welcome':
        subject = u'Welcome to Lost, your registration is completed.'
    else:
        raise ValueError('Unsupported e-mail template: {}'.format(template))

    tmpl = _ENV.get_template('email/{}.txt'.format(template))
    content = tmpl.render(**data)
    mail = Envelope(
        from_addr=(u'reservation@lost.lu', u'Lost.lu Registration Team'),
        to_addr=to,
        subject=subject,
        text_body=content)
    LOG.debug('Sending email out to {!r} via localhost'.format(to))
    mail.send('localhost')
