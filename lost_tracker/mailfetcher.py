from __future__ import print_function

from hashlib import md5
from os import makedirs
from os.path import exists, join
import logging

from backports import ssl
from gouge.colourcli import Simple
from imapclient import IMAPClient, SEEN, FLAGGED, create_default_context


LOG = logging.getLogger(__name__)
IMAGE_TYPES = {
    (b'image', b'jpeg')
}


def extract_elements(body, elements):
    if not body.is_multipart:
        elements.append(body)
    else:
        parts, relation = body
        if relation == 'alternative':
            elements.append(parts[0])
        else:
            for part in parts:
                extract_elements(part, elements)


def flatten_parts(body, start_index=0):
    output = []
    index = start_index
    for element in body:
        if element.is_multipart:
            output.extend(flatten_parts(element[0], index))
            index = output[-1][0] + 1
        else:
            output.append((index, element))
            index += 1
    return output


class MailFetcher(object):

    def __init__(self, host, username, password, use_ssl, image_folder,
                 force=False):
        self.host = host
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.image_folder = image_folder
        self.connection = None
        self.context = create_default_context()
        self.context.verify_mode = ssl.CERT_NONE
        self.force = force

    def connect(self):
        LOG.debug('Connecting to mail host...')
        self.connection = IMAPClient(self.host, use_uid=True, ssl=self.use_ssl,
                                     ssl_context=self.context)
        LOG.debug('Logging in...')
        self.connection.login(self.username, self.password)

    def fetch(self):
        LOG.debug('Fetching mail...')
        if not exists(self.image_folder):
            makedirs(self.image_folder)
            LOG.info('Created image folder at %r' % self.image_folder)

        self.connection.select_folder('INBOX')
        messages = self.connection.search(['NOT', 'DELETED'])
        response = self.connection.fetch(messages, ['FLAGS', 'BODY'])
        for msgid, data in response.items():
            is_read = SEEN in data[b'FLAGS']
            if is_read and not self.force:
                LOG.debug('Skipping already processed message #%r', msgid)
                continue
            else:
                # Add a "forced" note only if the message would not have been
                # processed otherwise.
                LOG.debug('Processing message #%r%s', msgid,
                          ' (forced override)' if is_read else '')
            body = data[b'BODY']
            el = []
            extract_elements(body, el)
            fetch_meta = [(i, data) for i, data in enumerate(el)
                          if (data[0], data[1]) in IMAGE_TYPES]
            if fetch_meta:
                self.download(msgid, fetch_meta)

    def in_index(self, md5sum):
        indexfile = join(self.image_folder, 'index')
        if not exists(indexfile):
            LOG.debug('%r does not exist. Assuming first run.', indexfile)
            return False
        hashes = [line.strip() for line in open(indexfile)]
        return md5sum in hashes

    def add_to_index(self, md5sum):
        if not md5sum.strip():
            return
        indexfile = join(self.image_folder, 'index')
        with open(indexfile, 'a+') as fptr:
            fptr.write(md5sum + '\n')

    def download(self, msgid, metadata):
        LOG.debug('Downloading images for mail #%r', msgid)
        has_error = False

        parts = flatten_parts(self.connection.fetch(
            [msgid], ['BODY'])[msgid]['BODY'][0])
        images = [part for part in parts if part[1][0] == 'image']
        for image_id, header in images:
            try:
                (major, minor, params, _, _, encoding, size) = header
                # Convert "params" into a more conveniend dictionary
                params = dict(zip(params[::2], params[1::2]))
                filename = params['name']
                unique_name = 'image_{}_{}_{}'.format(msgid, image_id, filename)
                encoding = encoding.decode('ascii')
                LOG.debug('Processing part #%r in mail #%r', image_id, msgid)
                element_id = 'BODY[%d]' % image_id
                response = self.connection.fetch([msgid], [element_id])
                content = response[msgid][element_id]
                if not content:
                    LOG.error('Attachment data was empty for '
                              'message #%r', msgid)
                    has_error = True
                    continue

                bindata = content.decode(encoding)
                md5sum = md5(bindata).hexdigest()
                if self.in_index(md5sum) and not self.force:
                    LOG.debug('Ignored duplicate file (md5=%s).', md5sum)
                    continue
                elif self.in_index(md5sum) and self.force:
                    LOG.debug('Bypassing index check (force=True)')

                fullname = join(self.image_folder, unique_name)
                if not exists(fullname) or self.force:
                    suffix = ' (forced overwrite)' if exists(fullname) else ''
                    with open(fullname, 'wb') as fptr:
                        fptr.write(bindata)
                    LOG.info('File written to %r%s', fullname, suffix)
                    self.add_to_index(md5sum)
                else:
                    has_error = True
                    LOG.warn('%r already exists. Not downloaded!' % fullname)
            except:
                LOG.error('Unable to process mail #%r', msgid, exc_info=True)
                has_error = True

        if has_error:
            self.connection.add_flags([msgid], FLAGGED)
        else:
            self.connection.add_flags([msgid], SEEN)


def run_cli():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Fetch photos from IMAP.')
    parser.add_argument('--verbose', '-v', dest='verbose',
                        default=0, action='count',
                        help='Prints actions on stdout.')
    parser.add_argument('--host', dest='host',
                        required=True,
                        help='IMAP Hostname')
    parser.add_argument('--login', '-l', dest='login',
                        required=True,
                        help='IMAP Username')
    parser.add_argument('--password', '-p', dest='password',
                        help='IMAP password.')
    parser.add_argument('--destination', '-d', dest='destination',
                        required=True,
                        help='The folder where files will be stored')
    parser.add_argument('--force', dest='force',
                        action='store_true', default=False,
                        help='Force fecthing mails. Even if they are read or '
                        'in the index')

    args = parser.parse_args()

    if args.verbose >= 2:
        Simple.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    elif args.verbose >= 1:
        Simple.basicConfig(level=logging.INFO, stream=sys.stdout)
    else:
        Simple.basicConfig(level=logging.WARNING)

    if not args.password:
        from getpass import getpass
        password = getpass('Password: ')
    else:
        password = args.password

    fetcher = MailFetcher(
        args.host,
        args.login,
        password,
        True,
        args.destination,
        args.force)
    try:
        fetcher.connect()
    except Exception as exc:
        print('Unable to connect: {}'.format(exc), file=sys.stderr)
        sys.exit(1)

    try:
        fetcher.fetch()
    except Exception as exc:
        print('Unable to fetch: {}'.format(exc), file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

if __name__ == '__main__':
    from getpass import getpass
    Simple.basicConfig(level=logging.DEBUG)
    fetcher = MailFetcher(
        input('Host: '),
        input('Login: '),
        getpass('Password: '),
        True,
        '/tmp/lost_images')
    fetcher.connect()
    fetcher.fetch()
