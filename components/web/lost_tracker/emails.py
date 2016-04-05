from collections import namedtuple
from smtplib import SMTPException
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


class Mailer(object):

    def send(self, template, to, data):
        subject, content = build_content(template, data)

        # Allow both User instances and tuples to be used as recipients
        recipients = []
        for recipient in to:
            if hasattr(recipient, 'email') and hasattr(recipient, 'name'):
                recipients.append((recipient.email, recipient.name))
            else:
                recipients.append(recipient)

        mail = Envelope(
            from_addr=('reservation@lost.lu', 'Lost.lu Registration Team'),
            to_addr='',
            cc_addr=('reservation@lost.lu', 'Lost.lu Registration Team'),
            subject=subject,
            text_body=content,
            bcc_addr=recipients)
        LOG.debug('Sending %r out to %r (BCC=%r),  via localhost',
                  mail,
                  mail.to_addr,
                  mail.bcc_addr)
        self._send(mail)

    def _send(self, mail):
        try:
            mail.send('localhost')
        except SMTPException:
            LOG.error("Unable to send email", exc_info=True)


class DummyMailer(Mailer):
    """
    A mailer class for testing. Does not actually send any e-mails. Prints
    emails to stdout instead.
    """
    LOG = logging.getLogger('%s.DummyMailer' % __name__)

    def _send(self, mail):
        print(mail)
