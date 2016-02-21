from __future__ import print_function
from hashlib import md5
from os import makedirs
from os.path import exists, join
import logging

from imapclient import IMAPClient, SEEN, FLAGGED, create_default_context
from backports import ssl


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


class MailFetcher(object):

    def __init__(self, host, username, password, use_ssl, image_folder):
        self.host = host
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.image_folder = image_folder
        self.connection = None
        self.context = create_default_context()
        self.context.verify_mode = ssl.CERT_NONE

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
            if SEEN in data[b'FLAGS']:
                LOG.debug('Skipping already processed message #%r', msgid)
                continue
            else:
                LOG.debug('Processing message #%r', msgid)
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
        for index, header in metadata:
            LOG.debug('Processing part #%r in mail #%r', index, msgid)
            index = index + 1
            try:
                (major, minor, params, _, _, encoding, size) = header
                encoding = encoding.decode('ascii')
                element_name = ('BODY[%d]' % index).encode('ascii')

                response = self.connection.fetch([msgid], [element_name])
                item = list(response.values())[0]
                bindata = item[element_name]
                md5sum = md5(bindata).hexdigest()
                if self.in_index(md5sum):
                    LOG.debug('Ignored duplicate file.')
                    continue

                params = dict(list(zip(params[0::2], params[1::2])))
                filename = params.get(b'name', b'')
                filename = filename.decode('ascii', errors='ignore')
                unique_name = 'image_{}_{}_{}'.format(msgid, index, filename)

                fullname = join(self.image_folder, unique_name)

                if not exists(fullname):
                    with open(fullname, 'wb') as fptr:
                        fptr.write(bindata)
                    LOG.info('File written to %r', fullname)
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

    args = parser.parse_args()

    if args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG, file=sys.stdout)
    elif args.verbose >= 1:
        logging.basicConfig(level=logging.INFO, file=sys.stdout)
    else:
        logging.basicConfig(level=logging.WARNING)

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
        args.destination)
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
    logging.basicConfig(level=logging.DEBUG)
    fetcher = MailFetcher(
        input('Host: '),
        input('Login: '),
        getpass('Password: '),
        True,
        '/tmp/lost_images')
    fetcher.connect()
    fetcher.fetch()
