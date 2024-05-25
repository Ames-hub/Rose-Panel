from toolbox.security import security
from quart import request as quart_request
from toolbox.pylog import pylog, logman
from toolbox.errors import error
from toolbox.storage import var
from quart_cors import cors
import multiprocessing
import datetime
import uvicorn
import quart
import os

# TODO: Fix.
def token_required(function):
    '''
    A Decorator for API funcs that makes sure the token is provided and valid.
    Also provides the user object to the function.
    '''
    async def wrapper(*args, **kwargs):
        data = await quart_request.get_json()

        # Check if the token is provided.
        token = data.get('token', None)
        if token is None:
            return {
                'message': 'Token not provided.'
            }, 401

        # Check if the token is valid.
        try:
            user = security.account(token=token, is_registering=False)
        except error.InvalidToken:
            return {
                'message': 'Invalid token.'
            }, 401
        except error.AccountNotFound:
            return {
                'message': 'Account not found.'
            }, 401
        except Exception as err:  # Catches all other errors.
            logging.error(f"Something went wrong! Error: {err}", exception=err)
            return {
                'message': 'something went wrong!'
            }, 401

        # Pass the user object to the function
        return await function(user, *args, **kwargs)

    wrapper.__name__ = function.__name__
    return wrapper

# The directory of the project.
project_dir = os.path.abspath(os.getcwd()) if __name__ == "__main__" else os.path.abspath(os.path.join(os.getcwd(), '..'))

logging = pylog(os.path.join(project_dir, 'logs', 'rose_%TIMENOW%.log'))
if __name__ == "__main__":
    logging.info(f"Rose Panel API started at {datetime.datetime.now()}.")

host_name = var.get('hostname', '0.0.0.0')
port_number = var.get('api//port', 5005)

app = quart.Quart(__name__)
app = cors(app, allow_origin="*", allow_headers="*")

class error_handlers:
    # Class doesn't do much more than make errors not result in No Returns.
    # Also provides a string message for the error.
    @app.errorhandler(error.AccountNotFound)
    def acc_not_found(err):
        return {
            'message': 'Account not found.'
        }, 401

    @app.errorhandler(error.AccountAlreadyExists)
    def acc_exists(err):
        return {
            'message': 'Account already exists.'
        }, 400

    @app.errorhandler(error.InvalidCredentials)
    def inv_cred(err):
        return {
            'message': 'Invalid credentials.'
        }, 400

    @app.errorhandler(error.InvalidToken)
    def inv_token(err):
        return {
            'message': 'Invalid token.'
        }, 401

    @app.errorhandler(error.MissingRequiredFields)
    def miss_req_fields(err):
        return {
            'message': 'Missing required fields.'
        }, 400

    @app.errorhandler(error.TooManyFields)
    def too_many_fields(err):
        return {
            'message': 'Too many fields provided.'
        }, 400

    @app.errorhandler(error.InsufficientPermissions)
    def insuf_perms(err):
        return {
            'message': 'Insufficient permissions.',
        }, 401

class rose_api:
    def run(use_ssl=False, silence=True):
        '''
        Call this function in a MP process to start the API.
        '''
        logging.info(f"Starting the RosePanel API on {host_name}:{port_number}.")

        # if silence is True, the uvicorn logs will not be displayed.
        if silence:
            logging.info("Silencing uvicorn logs.")
            uvicorn.config.LOGGING_CONFIG = logging

        if use_ssl:
            # Serve the app with SSL
            uvicorn.run(
                app,
                host=host_name,
                port=port_number,
                ssl_certfile='toolbox/certificate.pem',
                ssl_keyfile='toolbox/private.key'
            )
        else:
            # Serve the app without SSL
            uvicorn.run(
                app,
                host=host_name,
                port=port_number
            )

    @app.route("/api")
    async def index():
        return {
            'timenow': datetime.datetime.now().timestamp(),
            'status': 'ok'
        }, 200

    @app.route("/api/validate_token", methods=["POST"])
    async def validate_token():
        post_data = await quart_request.get_json()
        token = post_data.get('token', None)
        if token is None:
            return {
                'message': 'Missing required fields.'
            }, 400

        try:
            user = security.account(token=token, is_registering=False)
        except:
            return 'bad', 401

        if user.current_session == token:
            return 'ok', 200
        else:
            return 'bad', 401

    @app.route("/api/login", methods=["POST"])
    async def login():
        post_data = await quart_request.get_json()

        email_address = post_data.get('email_address', None)
        password = post_data.get('password', None)
        is_registering = post_data.get('is_registering', None)

        # Validate data
        if email_address is None or password is None:
            return {
                'message': 'Missing required fields.'
            }, 400
        if is_registering is None or type(is_registering) is not bool:
            return {
                'message': 'specify if the user is registering or logging in.'
            }, 400

        # This also handles registration and login
        try:
            user = security.account(email_address=email_address, password=password, is_registering=is_registering)
        except (error.InvalidCredentials, error.AccountNotFound, error.AccountAlreadyExists) as err:
            return {
                'message': str(err)
            }, 400

        token = user.get_token()
        logging.info(f"User '{email_address}' has successfully logged in.")

        return {
            'token': token
        }, 200

    @app.route("/api/servers/list", methods=["POST"])
    async def list_servers():
        data = await quart_request.get_json()
        token = data.get('token', None)

        user = security.account(token=token)
        servers = user.list_servers(own_servers_only=True)  # Await the async operation here
        return {
            'servers': servers
        }, 200

    @app.route("/api/servers/create", methods=["POST"])
    async def create_server():
        data = await quart_request.get_json()
        token = data.get('token', None)

        user = security.account(token=token)
        user.create_server(
            identifier=data.get('identifier', None),
            description=data.get('description', None),
            install_cmds=data.get('install_cmds', None),
            kill_signal=data.get('kill_signal', None),
            init_cmd=data.get('init_cmd', None),
            hostname=data.get('hostname', None),
            port=data.get('port', None)
        )
        return {
            'message': 'Server created successfully.'
        }, 200

    @app.route("/api/accounts/permissions", methods=["POST"])
    async def get_my_perms():
        data = await quart_request.get_json()
        token = data.get('token', None)

        user = security.account(token=token)
        return {
            'permissions': user.permissions
        }, 200

if __name__ == "__main__":
    LOGMAN_Thread = multiprocessing.Process(target=logman)
    LOGMAN_Thread.start()

    app.run() # Start the API in debug mode if this script is run directly.
    LOGMAN_Thread.kill() # Kill the logman thread when the API is stopped.
