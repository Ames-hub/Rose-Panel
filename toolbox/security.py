# This python library handles session tokens and accounts.
from toolbox.thorns import thorns
from toolbox.storage import var, dt
from toolbox.errors import error
from toolbox.pylog import pylog
import datetime
import secrets
import re
import os

logging = pylog(filename='logs/rose_%TIMENOW%.log')
settings_path = os.path.join(os.getcwd(), 'settings.json')

# noinspection PyCallingNonCallable
class security:
    def __init__(self):
        pass

    def sanitize(input_string):
        """
        Sanitizes input by removing potentially harmful characters.

        :param input_string: The input string to sanitize.
        :return: The sanitized input string.
        """
        # Define a regular expression pattern to match potentially harmful characters
        pattern = re.compile(r'[^\w\s@.-]', re.UNICODE)

        # Use the pattern to replace any matches with an empty string
        sanitized_string = re.sub(pattern, '', input_string)

        return sanitized_string

    class perms:
        '''
        Uses bitwise operations to determine permissions.
        If you wish to add more permissions, add them to the class and increment the right-most value by 1.
        '''
        ADMINISTRATOR = 1 << 0
        LIST_SERVERS = 1 << 1
        LIST_OTHERS_SERVERS = 1 << 2
        MAKE_SERVERS = 1 << 3
        DELETE_SERVERS = 1 << 4
        EDIT_SERVERS = 1 << 5

        def prechecks(func):
            # noinspection PyUnresolvedReferences,PyCallingNonCallable
            def wrapper(*args, **kwargs):
                # Step 1: Put all arguments into a dictionary
                arguments = dict(zip(func.__code__.co_varnames, args))
                arguments.update(kwargs)

                # Step 2: Check if 'token' is in the arguments
                if 'token' in arguments:
                    # Step 3: Check if the token is valid
                    valid_tokens = ['token1', 'token2', 'token3']  # Example list of valid tokens
                    if arguments['token'] not in valid_tokens:
                        raise ValueError("Invalid token")

                # Call the original function with the arguments
                return func(*args, **kwargs)

            return wrapper

        def check_permitted(perms_needed:list, users_perms:list=None) -> tuple:
            '''
            Used to make sure the user has ALL the required permissions to continue.
            If successful, returns True and None, else returns False and the missing perm.
            '''
            # Check if the user is an administrator. If they are, they have all permissions.
            if security.perms.ADMINISTRATOR in users_perms:
                return True, None

            # Check if the user has the required permissions.
            for perm in perms_needed:
                if perm not in users_perms:
                    return False, perm
            return True, None

        def require(needed_perms:list, func):
            # noinspection PyUnresolvedReferences,PyCallingNonCallable
            def wrapper(*args, **kwargs):
                # Put all arguments into a dictionary
                arguments = dict(zip(func.__code__.co_varnames, args))
                arguments.update(kwargs)

                if 'token' in arguments:
                    # Check if the token is valid
                    if arguments['token'] not in dict(var.get('tokens', {})).keys():
                        raise error.InvalidToken(f"Token \"{arguments.get('token')}\" not valid or non-existant.")
                    else:
                        account = security.account(token=arguments['token'])
                else:
                    # Check if the email and password are valid
                    email_address = arguments.get('email', None) or arguments.get('email_address', None)
                    password = arguments.get('password', None) or arguments.get('pass', None)

                    if email_address is None:
                        raise error.MissingRequiredFields(fields="Email address")
                    if password is None:
                        raise error.MissingRequiredFields(fields="Password")

                    # Check if the account exists
                    account = security.account(email_address=email_address, password=password)

                # Call the original function with the arguments
                security.perms.check_permitted(needed_perms, account.permissions)

                return func(*args, **kwargs)
            return wrapper

        def parse_for_file(user_permissions:list) -> dict:
            '''
            Formats the permissions for the file.
            This is useful when saving the permissions to a file.

            :param user_permissions: The permissions of the user.
            :return formatted_permissions: The formatted permissions.
            '''
            assert type(user_permissions) is list, 'User permissions must be a list.'
            if user_permissions is None:
                return {}

            # Define all possible permissions
            all_permissions = security.perms.__dict__.values() # Get all the values of the perms class.

            # Filter out the ones that are not integers. (eg, the __doc__ value or the format_permissions function)
            all_permissions = [perm for perm in all_permissions if type(perm) is int]

            # Create a dictionary to store formatted permissions
            formatted_permissions = {}

            # Loop through all possible permissions
            for permission in all_permissions:
                # Check if the user has the permission
                if permission in user_permissions:
                    formatted_permissions[permission] = True
                else:
                    formatted_permissions[permission] = False

            return formatted_permissions

        def parse_to_list(formatted_permissions:dict) -> list:
            '''
            Parses the permissions from a dictionary to a list.

            :param formatted_permissions: The formatted permissions.
            :return user_permissions: The permissions of the user.
            '''
            if formatted_permissions is None:
                return []

            user_permissions = []
            for permission, value in formatted_permissions.items():
                if value is True:
                    user_permissions.append(permission)
            return user_permissions

        def save_permissions(email_address:str, permissions:dict) -> bool:
            '''
            Saves the permissions to the user's account.

            :param email_address: The email address of the user.
            :param permissions: The permissions to save.
            '''
            email = security.sanitize(email_address)
            var.set(f'accounts//{email}//permissions', permissions, file=settings_path)
            return True

    class sessions:
        def new(email_address:str, do_save:bool=True) -> str:
            '''
            Generates a new session token for the user.

            :param do_save: Whether or not to save the token to the memory file.
            :return token: The generated token.
            '''
            email_address = security.sanitize(email_address)

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
                security.sessions.save(token, email_address)

            logging.info(f"New Session {token} Created for {email_address}")
            return token

        def find(email_address):
            '''
            Finds the token of the user.

            :param email_address: The email address of the user.
            :return token: The token of the user.
            '''
            email_address = security.sanitize(email_address)
            token = var.get(f'accounts//{email_address}//current_session')
            return token

        def save(token:str, email_address:str, expire_in:datetime.timedelta=datetime.timedelta(hours=4)) -> bool:
            '''
            Saves the token to the memory file.

            :param email_address: The email address of the user.
            :param expire_in: The time until the token expires.
            :return:
            '''
            email_address = security.sanitize(email_address)

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
            token = security.sanitize(token)

            # Finds who the token belongs to
            email = var.get(f'tokens//{token}//belongs_to')

            # Deletes the token
            var.delete(f'tokens//{token}')

            # Removes the 'current_session' from the user's account

            var.set(f'accounts//{email}//current_session', None, file=settings_path)
            logging.info(f"Session {token} Deleted for {email}")

            return True

    class account:
        def __init__(self, email_address:str=None, password:str=None, token:str=None, is_registering=False):
            '''
            Register or Login to a user account.

            :param email_address:
            :param password:
            :param is_registering:`
            :param token:
            '''
            if (email_address is None and password is None) and token is None:
                raise error.MissingRequiredFields('email_address and password or token must be provided.')

            # If a token is provided, then we can skip the login process.
            if token is not None:
                token = security.sanitize(token) # Sanitize the token incase it's been tampered with.
                # Check if the account exists.
                email_address = var.get(f"tokens//{token}//belongs_to")
                if email_address is None:
                    raise error.AccountNotFound(email_address)
                self.email_address = email_address
                self.current_session = token
                self.password = var.get(f"accounts//{email_address}//password")
                self.permissions = security.perms.parse_to_list(
                    var.get(f"accounts//{email_address}//permissions")
                )
                return

            # Makes sure input is safe.
            email_address = security.sanitize(email_address)
            password = security.sanitize(password)

            # Enter the loop to register or login.
            while True:
                """
                Loops here so that if the user registers, they can register and then immediately 'login'
                
                Here's the flow.
                1. User tries to login with 'is_registering' set to True.
                2. The account is created in the 'else' block.
                3. 'is_registering' is set to False.
                4. The loop continues, returning before the if-else block, but this time the user is trying to login with
                'is_registering' set to False.
                5. The user logs in with the newly created account.
                6. The loop breaks, allowing the user to continue.
                """
                if not is_registering:
                    # Essentially login code. Checks password and email are fine, which then makes getting a token easy.
                    self.email_address = email_address
                    self.current_session = None
                    self.password = password
                    self.permissions = security.perms.parse_to_list(
                        var.get(f"accounts//{email_address}//permissions")
                    )
                    # Check if the account exists.
                    try:
                        var.get(f"accounts//{email_address}")
                    except KeyError:
                        raise error.AccountNotFound(email_address)

                    saved_password = var.get(f"accounts//{email_address}//password")
                    # Check if the password is correct.
                    if password != saved_password or password is None:
                        raise error.InvalidCredentials(email_address, password)
                    break
                else:
                    # Checks if the account already exists.
                    if var.get(f"accounts//{email_address}") is not None:
                        raise error.AccountAlreadyExists(email_address)
                    # Register the account.
                    account = dt.ACCOUNT
                    account['password'] = password
                    account['email_address'] = email_address
                    var.set(f'accounts//{email_address}', account, file=settings_path)
                    is_registering = False
                    # User always starts with no permissions.
                    logging.info(f"Account {email_address} Created")
                    continue
            logging.info(f"Account {email_address} Logged In")

        def get_token(self) -> bool:
            '''
            Attempts to login with the provided credentials.
            '''
            # Generate a new session token.
            token = security.sessions.new(self.email_address)

            # saves it to the class.
            self.current_session = token

            return token

        def logout(self) -> bool:
            '''
            Logs out the account with the specified token.
            '''
            # Check if the account exists.
            token = var.get(f"accounts//{self.email_address}//current_session")
            if token is None:
                return False

            # Delete the token.
            security.sessions.delete(token)
            self.current_session = None
            logging.info(f"Account {self.email_address} Logged Out")

            return True

        def list_servers(self, own_servers_only=True):
            '''
            Lists the servers of the user.

            :param own_servers_only: Whether or not to list only the user's servers or all they are allowed to see.
            '''
            result = security.perms.check_permitted([security.perms.LIST_SERVERS], self.permissions)
            if not result:
                raise error.InsufficientPermissions(result[1])

            server_list = os.listdir('servers')
            processed_server_list = {}
            for server_id in server_list:
                servers_data = var.load_all(file=f'servers/{server_id}/config.json')
                if own_servers_only:
                    if servers_data['owner'] != self.email_address:
                        continue
                processed_server_list[server_id] = servers_data
            '''
            NOTE: THis is an example of what the processed_server_list would look like.
            (Important data only shown here. You'll find the full dict in storage.py > DT > SERVER_INSTANCE)
            
            {
                'Wordy server': {
                    'online': True,
                    'description': 'This is another test server about bread. Bread is amazing',
                    'owner': self.email_address,
                    'resources': { # Percentages of resources used.
                        'RAM': {'used': 211, 'total': 524},
                        'CPU': {'used': 14, 'allowed': 50}, # allowed to use 50% of the CPU and no more.
                        'STORAGE': {'used': 256, 'total': 1024}
                    }
                }
            }
            '''

            # Returns test data
            return processed_server_list

        def create_server(self, identifier, description, init_cmd, kill_signal, install_cmds:list, hostname:str, port:int):
            thorns.create(
                identifier=identifier,
                description=description,
                owner_email=self.email_address,
                init_cmd=init_cmd,
                kill_signal=kill_signal,
                install_cmds=install_cmds,
                hostname=hostname,
                port=port
            )

        def start_server(self, server_id):
            thorns.start(server_id, self.email_address)

        def stop_server(self, server_id):
            thorns.stop(server_id, self.email_address)
