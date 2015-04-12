from hashlib import md5
from os import makedirs
from os.path import exists, join
import logging

from imapclient import IMAPClient, SEEN, FLAGGED


LOG = logging.getLogger(__name__)
IMAGE_TYPES = {
    ('image', 'jpeg')
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

    def __init__(self, host, username, password, ssl, image_folder):
        self.host = host
        self.username = username
        self.password = password
        self.ssl = ssl
        self.image_folder = image_folder
        self.connection = None

    def connect(self):
        self.connection = IMAPClient(self.host, use_uid=True, ssl=self.ssl)
        self.connection.login(self.username, self.password)

    def fetch(self):
        if not exists(self.image_folder):
            makedirs(self.image_folder)
            LOG.info('Created image folder at %r' % self.image_folder)

        self.connection.select_folder('INBOX')
        messages = self.connection.search(['NOT DELETED'])
        response = self.connection.fetch(messages, ['FLAGS', 'BODY'])
        for msgid, data in response.iteritems():
            if SEEN in data['FLAGS']:
                LOG.debug('Skipping already processed message #%r', msgid)
                continue
            body = data['BODY']
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
                element_name = 'BODY[%d]' % index

                response = self.connection.fetch([msgid], [element_name])
                item = response.values()[0]
                bindata = item[element_name].decode(encoding)
                md5sum = md5(bindata).hexdigest()
                if self.in_index(md5sum):
                    LOG.debug('Ignored duplicate file.')
                    continue

                params = dict(zip(params[0::2], params[1::2]))
                filename = params.get('name', '')
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


if __name__ == '__main__':
    from getpass import getpass
    logging.basicConfig(level=logging.DEBUG)
    fetcher = MailFetcher(
        raw_input('Host: '),
        raw_input('Login: '),
        getpass('Password: '),
        True,
        '/tmp/lost_images')
    fetcher.connect()
    fetcher.fetch()
