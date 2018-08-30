import os
import unittest
import uuid

from utils import redact_email, new_iv, encrypt, decrypt


class TestRefreshTokenEncryption(unittest.TestCase):
    pass


class TestEmailRedaction(unittest.TestCase):

    @staticmethod
    def _test_regular_email(email):
        user, domain = email.split('@')
        redacted = redact_email(email)
        # make sure the user is still in the redacted email
        assert user in redacted
        # make sure the tail of the TLD is in the redacted email
        assert domain[-3:] in redacted
        # make sure no other parts of the domain make it into the redacted email
        assert len(redacted.split('.')[-1]) <= len(domain.split('.')[-1])

    def test_regular_emails(self):
        regular_emails = ['foobar@example.com',
                          'reallyreallyreallyreallyreallylongusername@a.pretty.long.domain.edu',
                          'emailwithreallyshortdomain@g.cn',
                          'a@example.com' ]
        for email in regular_emails:
            self._test_regular_email(email)

    @staticmethod
    def _test_broken_email(email):
        redacted = redact_email(email)
        assert '****' in redacted

    def test_broken_emails(self):
        broken_emails = ['thisisnotanemail',
                         'neitheris@this',
                         '',
                         'blash']
        for email in broken_emails:
            self._test_broken_email(email)


class TestTokenEncryption(unittest.TestCase):
    """
    To avoid having to set up a whole flask testing framework
    only for this PR, we will just do some simple encryption tests
    that don't actually use a cookie but that do verify that the
    encryption mechanisms work.

    These are mostly just sanity checks to ensure I'm using the
    crypto library properly
    """
    varname = 'REFRESH_TOKEN_ENCRYPT_KEY'

    def setUp(self):
        os.environ[self.varname] = 'This string is 32 character long'
        pass

    def test_encryption_does_something(self):
        iv = new_iv()
        random_test_string = str(uuid.uuid4())
        assert random_test_string not in encrypt(random_test_string, iv)

    def test_new_iv(self):
        iv1 = new_iv()
        iv2 = new_iv()
        random_test_string = str(uuid.uuid4())
        assert encrypt(random_test_string, iv1) != encrypt(random_test_string, iv2)

    def test_decrypt(self):
        iv = new_iv()
        random_test_string = str(uuid.uuid4())
        assert decrypt(encrypt(random_test_string, iv), iv) == random_test_string

    def test_decrypt_with_bad_key(self):
        iv = new_iv()
        random_test_string = str(uuid.uuid4())
        secret = encrypt(random_test_string, iv)
        os.environ[self.varname] = 'a different 32 chars long string'
        mangled_output = decrypt(secret, iv)
        assert mangled_output != random_test_string
