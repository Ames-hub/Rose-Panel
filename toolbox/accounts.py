from toolbox.permissions import permissions as perms
from toolbox.storage import var, settings_path, dt
from toolbox.security import sanitize
from toolbox.sessions import sessions
from toolbox.thorns import thorns
from toolbox.errors import error
from toolbox.pylog import pylog
import os

logging = pylog(filename='logs/rose_%TIMENOW%.log')

class user_account:
    def __init__(self, email_address: str = None, password: str = None, token: str = None, is_registering=False):
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
            token = sanitize(token)  # Sanitize the token incase it's been tampered with.
            # Check if the account exists.
            email_address = var.get(f"tokens//{token}//belongs_to")
            if email_address is None:
                raise error.AccountNotFound(email_address)
            self.email_address = email_address
            self.current_session = token
            self.password = var.get(f"accounts//{email_address}//password")
            self.permissions = perms.load(email_address)
            return

        # Makes sure input is safe.
        email_address = sanitize(email_address)
        password = sanitize(password)

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
                self.permissions = perms.load(email_address)
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
        token = sessions.new(self.email_address)

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
        sessions.delete(token)
        self.current_session = None
        logging.info(f"Account {self.email_address} Logged Out")

        return True

    def list_servers(self, own_servers_only=True):
        '''
        Lists the servers of the user.

        :param own_servers_only: Whether or not to list only the user's servers or all they are allowed to see.
        '''
        perms.require(
            [perms.LIST_SERVERS],
            email_address=self.email_address
        )
        if own_servers_only is not True:
            perms.require(
                [perms.LIST_OTHERS_SERVERS],
                email_address=self.email_address
            )

        server_list = os.listdir('servers')
        processed_server_list = {}
        for server_id in server_list:
            servers_data = var.load_all(file=f'servers/{server_id}/config.json')
            if own_servers_only:
                if servers_data['owner'] == self.email_address:
                    server_name = thorns.get_idtype_target(server_id, 'name')
                    processed_server_list[server_name] = servers_data
                continue
            else:
                server_name = thorns.get_idtype_target(server_id, 'name')
                processed_server_list[server_name] = servers_data
        '''
        NOTE: THis is an example of what the processed_server_list would look like.
        (Only some data only shown here. You'll find the full dict in storage.py > class DT > SERVER_INSTANCE)

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

    def create_server(
            self,
            identifier,
            description,
            init_cmd,
            kill_signal,
            install_cmds: list,
            hostname: str,
            port: int
    ):
        assert isinstance(hostname, str), "hostname must be a string."
        assert isinstance(kill_signal, (str, int)), "kill_signal must be a string or an integer."
        assert isinstance(init_cmd, str), "init_cmd must be a string."
        assert isinstance(install_cmds, list), "install_cmds must be a list."
        return thorns.create(
            identifier=identifier,
            description=description,
            owner_email=self.email_address,
            init_cmd=init_cmd,
            kill_signal=kill_signal,
            install_cmds=install_cmds,
            hostname=hostname,
            port=port
        )

    def delete_server(self, name_id: str):
        suid = thorns.get_idtype_target(name_id, 'suid')
        return thorns.delete(suid, self.email_address)

    def start_server(self, identifier):
        suid = thorns.get_idtype_target(identifier, 'suid')
        return thorns.start(suid, self.email_address)

    def stop_server(self, name_id):
        suid = thorns.get_idtype_target(name_id, 'suid')
        return thorns.stop(suid, self.email_address)
