from toolbox.storage import var, dt, settings_path
from toolbox.security import sanitize
from toolbox.pylog import pylog
import secrets
import datetime

logging = pylog(filename='logs/rose_%TIMENOW%.log')

class sessions:
    def new(email_address:str, do_save:bool=True) -> str:
        '''
        Generates a new session token for the user.

        :param do_save: Whether or not to save the token to the memory file.
        :return token: The generated token.
        '''
        email_address = sanitize(email_address)

        # if bool(os.getenv('ONE_TOKEN_ACCOUNTS')) is True or var.get("one_token_accounts") is True:
        if var.get("one_token_accounts") is True:
            # Check if the user already has a token.
            token = var.get(f'accounts//{email_address}//current_session')
            if token is not None:
                logging.info(f"Session {token} Continued for {email_address}")
                return token

        # Generate a new token.
        token = secrets.token_urlsafe(64)

        # Makes sure that the token does not have a / in it.
        while '/' in token:
            token = secrets.token_urlsafe(64)

        # Save the token to the memory file if specified.
        if do_save:
            sessions.save(token, email_address)

        logging.info(f"New Session {token} Created for {email_address}")
        return token

    def find(email_address):
        '''
        Finds the token of the user.

        :param email_address: The email address of the user.
        :return token: The token of the user.
        '''
        email_address = sanitize(email_address)
        token = var.get(f'accounts//{email_address}//current_session')
        return token

    def save(token:str, email_address:str, expire_in:datetime.timedelta=datetime.timedelta(hours=4)) -> bool:
        '''
        Saves the token to the memory file.

        :param email_address: The email address of the user.
        :param expire_in: The time until the token expires.
        :return:
        '''
        email_address = sanitize(email_address)

        token_dict = dt.TOKEN_DICT
        token_lifespan = var.get('token_lifespan')
        if token_lifespan is int:
            # Convert the token lifespan to a timedelta object.
            expire_in = datetime.timedelta(seconds=token_lifespan)

        # Dict is filled with None by default. Sets the values we need.
        token_dict['expire_on'] = (datetime.datetime.now() + expire_in).timestamp() # int/float for json file.
        token_dict['belongs_to'] = email_address
        token_dict['activity'] = {'session_created': datetime.datetime.now().timestamp()} # same reason as above.
        var.set(f'tokens//{token}', token_dict, file=settings_path)
        var.set(f'accounts//{email_address}//current_session', token, file=settings_path)
        return True

    def delete(token:str) -> bool:
        '''
        Deletes the token from the memory file.

        :param token: The token to delete.
        '''
        token = sanitize(token)

        # Finds who the token belongs to
        email = var.get(f'tokens//{token}//belongs_to')

        # Deletes the token
        var.delete(f'tokens//{token}')

        # Removes the 'current_session' from the user's account

        var.set(f'accounts//{email}//current_session', None, file=settings_path)
        logging.info(f"Session {token} Deleted for {email}")

        return True
