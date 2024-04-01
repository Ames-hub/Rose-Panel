# This python library handles session tokens and accounts.
import datetime
import secrets
import json
settings_file = 'settings.txt'

tokens = {}

class sessions:
    def persist_old_token(token:str, token_dict:dict):
        '''Persists tokens by adding them to a json file in `data/persisted_tokens.json` (this is to save their logs)'''


    def new(email_address:str, do_save:bool=True) -> str:
        token = secrets.token_urlsafe(256)
        if do_save:
            sessions.save(token, email_address)
        return token

    def save(token:str, email_address:str, expire_in:datetime.date=datetime.date(day=7, month=0, year=0)) -> bool:
        token_dict = {
            'activity': {}, # Logs for this session token
            'expire_on': datetime.date.today() + expire_in,
            'belongs_to': email_address
        }
        try:
            tokens[token] = token_dict
        # Catches the token already existing.
        except KeyError:
            return False
        return True

    def delete(token:str) -> bool:
        try:
            del tokens[token]
        except KeyError:
            return False
        return True
