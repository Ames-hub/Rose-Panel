# This python library handles session tokens and accounts.
import secrets, random
settings_file = 'settings.txt'

class sessions:
    def new():
        token = secrets.token_urlsafe(256)
        return token

    def save(token):
        # todo: use jmod to save a token to a sessions list.
        raise NotImplementedError
