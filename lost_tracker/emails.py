from collections import namedtuple
import logging

from envelopes import Envelope
from jinja2 import Environment, PackageLoader

_ENV = Environment(loader=PackageLoader('lost_tracker', 'templates'))
LOG = logging.getLogger(__name__)
MailData = namedtuple('MailData', 'subject body')


def build_content(template, data):
    if template == 'registration_check':
        subject = u'New registration for {0.name}'.format(data['group'])
    elif template == 'confirm':
        subject = u'Please confirm your registration for lost.lu'
    elif template == 'registration_update':
        subject = u'Lost Registration Change'
    elif template == 'welcome':
        subject = u'Welcome to Lost, your registration is completed.'
    elif template == 'new_message':
        subject = u'New message on lost.lu'
    else:
        raise ValueError('Unsupported e-mail template: {}'.format(
            template))

    tmpl = _ENV.get_template('email/{}.txt'.format(template))
    content = tmpl.render(**data)
    return MailData(subject, content)


class DummyMailer(object):
    """
    A mailer class for testing. Does not actually send any e-mails. Prints
    emails to stdout instead.
    """
    LOG = logging.getLogger('%s.DummyMailer' % __name__)

    def send(self, template, to, data):
        subject, body = build_content(template, data)
        self.LOG.info("DummyMailer called with template=%r, to=%r, data=%r" % (
            template, to, data))
        print(u'Sending Mail'.center(80, '-'))
        print(u'To:')
        for recipient in to:
            print(u'    %r' % str(recipient))
        print(u'Subject: %r' % subject)
        print(u'Body'.center(80, '-'))
        print(body)
        print(u'End of Mail'.center(80, '-'))


class Mailer(object):

    def send(self, template, to, data):
        subject, content = build_content(template, data)
        mail = Envelope(
            from_addr=('reservation@lost.lu', 'Lost.lu Registration Team'),
            to_addr=to,
            subject=subject,
            text_body=content)
        LOG.debug('Sending email out to {!r} via localhost'.format(to))
        mail.send('localhost')
