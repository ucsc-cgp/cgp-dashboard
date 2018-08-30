import os

from Crypto import Random
from Crypto.Cipher import AES


def redact_email(email):
    """
    cut out the domain for an email if there is one

    We still show up to 4 character of the top level domain (including the .)
    For everything else in the domain, just replace with ***
    Return '****' if email is misformatted
    """
    if len(email.split('@')) != 2:
        return '****'
    user, host = email.split('@')
    tld = host.split('.')[-1]
    if len(host.split('.')) < 2:
        return user + '@' + '****'
    return user + '@' + '***' + ('.' + tld)[-4:]


def new_iv():
    """generate a new initialization vector for AES"""
    return Random.new().read(AES.block_size)


def decrypt(value, iv):
    key = os.getenv('REFRESH_TOKEN_ENCRYPT_KEY')
    if key is None:
        raise ValueError('There is no encryption key set for the refresh token. '
                         'Something was misconfigured!')
    cipher = AES.new(key, AES.MODE_CFB, iv)
    return cipher.decrypt(value)


def encrypt(value, iv):
    key = os.getenv('REFRESH_TOKEN_ENCRYPT_KEY')
    if key is None:
        raise ValueError('There is no encryption key set for the refresh token. '
                         'Something was misconfigured!')
    cipher = AES.new(key, AES.MODE_CFB, iv)
    return cipher.encrypt(value)
