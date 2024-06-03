from toolbox.storage import var, dt
from toolbox.pylog import pylog
import multiprocessing
import subprocess
import inspect
import random
import shutil
import signal
import shlex
import os

logging = pylog('logs/rose_%TIMENOW%.log')
os.makedirs('servers', exist_ok=True)

DEBUG = os.environ.get('DEBUG', False)
maximum_args = 4

class thorns:
    class errors:
        '''
        Custom errors for the thorns module.
        These do not serve any purpose other than to make the code more
        readable and being more specific when it all goes wrong.
        '''
        class ServerExists(Exception):
            def __init__(self, msg):
                self.msg = msg

        class ServerDoesNotExist(Exception):
            def __init__(self, msg):
                self.msg = msg

    def validate_data(data:dict):
        '''
        Raises an error if the data is invalid. Should be called before all other functions.
        '''
        assert data is not None, "data is None."
        assert isinstance(data, dict), "data is not a dictionary."
        assert len(data.keys()) != 0, f"No arguments provided."
        if 'identifier' in data.keys():
            assert data.get('identifier', None) is not None, "identifier is None."
            assert isinstance(data.get('identifier', None), str), "identifier is not a string."
            assert data.get('identifier', None) != '', "identifier is an empty string."

    def check_exists(suid=None, name_id=None):
        if suid is not None and name_id is None:
            return os.path.exists(f'servers/{suid}') is True
        elif suid is None and name_id is not None:
            for server in os.listdir('servers'):
                server_identifier = var.get('identifier', file=f'servers/{server}/config.json', dt_default=dt.SERVER_INSTANCE)
                if server_identifier == name_id:
                    return True
        else:
            raise ValueError("suid and name_id cannot both be None or both be not None.")

    def get_opposite_id(suid=None, name_id=None):
        '''
        This function gets the opposite of the provided id. If the suid is provided, it will return the name_id.
        If the name_id is provided, it will return the suid.
        :param suid: The server unique id.
        :param name_id: The name id.
        :return str: The opposite id.
        '''
        if suid is not None and name_id is None:
            return var.get('identifier', file=f'servers/{suid}/config.json', dt_default=dt.SERVER_INSTANCE)
        elif suid is None and name_id is not None:
            for server in os.listdir('servers'):
                server_identifier = var.get('identifier', file=f'servers/{server}/config.json', dt_default=dt.SERVER_INSTANCE)
                if server_identifier == name_id:
                    return server
        else:
            raise ValueError("suid and name_id cannot both be None or both be not None.")

    def compile_data_from_func() -> dict:
        '''
        This function takes all the arguments provided to the calling function and returns them as a dictionary.
        via the inspection module.
        '''
        current_frame = inspect.currentframe()
        previous_frame = current_frame.f_back
        arg_info = inspect.getargvalues(previous_frame)
        data = {k: v for k, v in arg_info.locals.items() if k in arg_info.args}
        return data

    def get_id_type(identifier:str) -> str:
        if identifier.startswith('thorn_'):
            return 'suid'
        else:
            return 'name'

    def get_idtype_target(identifier:str, target_type:str) -> str:
        '''
        This function returns the type of the identifier specified for that server.
        So if you provide a SUID with the target type being suid, it will return the SUID.
        If you provide a SUID with the target type being name, it will return the name id.
        and vice versa.

        :param identifier: The identifier of the server.
        :param target_type: The type you want to get. (suid or name)
        :return:
        '''
        assert type(identifier) is str, f'identifier must be a string. Not {identifier} {type(identifier)}'
        assert target_type in ['suid', 'name'], "target_type must be either 'suid' or 'name'."
        if target_type == 'suid':
            if identifier.startswith('thorn_'):
                return identifier
            else:
                return thorns.get_opposite_id(name_id=identifier)
        elif target_type == 'name':
            if not identifier.startswith('thorn_'):
                return identifier
            else:
                return thorns.get_opposite_id(suid=identifier)
        else:
            raise ValueError("target_type must be either 'suid' or 'name'.")

    # TODO: Fix this function. Figure out why the subprocess.Popen never starts the process.
    def worker(identifier, input_pipe: multiprocessing.Pipe, DEBUG=False) -> bool:
        '''
        This function is used to run a command in a separate process in a certain directory. AKA The backbone of Thorns.
        Writes to a file in server/identifier/stdout which is text-based. This is used to read the output of the server.

        :param identifier: The identifier of the server.
        :param input_pipe: The pipe to send input to the subprocess.
        :param DEBUG: Whether to run in debug mode or not.
        :return bool: True if the server was started successfully, False if it was not.
        '''
        identifier = thorns.get_idtype_target(identifier, 'suid')
        content_dir = var.get('content_dir', file=f'servers/{identifier}/config.json', dt_default=dt.SERVER_INSTANCE)
        project_wd = var.get('working_directory')
        project_wd = os.path.abspath(project_wd)

        server_file = os.path.join(project_wd, f'servers/{identifier}/config.json')
        # Loads the init command from the server file and splits it into a list.
        init_cmd = str(dict(var.load_all(file=server_file, dt_default=dt.SERVER_INSTANCE))['init_cmd']).split(" ")

        if DEBUG is True:
            logging.debug(f'Running command: {init_cmd}')
            logging.debug(f'Working directory: {os.getcwd()}')
            logging.debug(f'Content directory: {content_dir}')
            logging.debug(f'Server file: {server_file}')
            logging.debug(f'Project working directory: {project_wd}')

        process = subprocess.Popen(
            args=init_cmd,
            start_new_session=True,
            cwd=project_wd,
        )

        var.set(key='process_pid', value=process.pid, file=server_file, dt_default=dt.SERVER_INSTANCE)
        var.set(key='online', value=True, file=server_file, dt_default=dt.SERVER_INSTANCE)

        if DEBUG is True:
            if process.pid is not None:
                logging.debug(f'Server {identifier} started successfully.')
            else:
                logging.debug(f'Server {identifier} did not start successfully.')

        # Ends the process
        var.set(key='process_pid', value=None, file=server_file, dt_default=dt.SERVER_INSTANCE)
        var.set(key='online', value=False, file=server_file, dt_default=dt.SERVER_INSTANCE)
        return True

    def create(identifier:str,
               description:str,
               owner_email:str,
               init_cmd:str,
               install_cmds:list,
               kill_signal,
               port=None,
               max_ram=1024, max_cpu=-1, max_storage=2048, # MiB and CPU is "allowed" percentage. -1 is unlimited.
               hostname="0.0.0.0") -> bool:
        '''
        Creates a new server instance.

        :param description: The description of the server.
        :param owner_email: The email of the person trying to make the server.
        :param init_cmd: The command to run to start the server. (such as "python3 test.py -O")
        :param install_cmds: A list of all commands needed to install the server.
        :param kill_signal: The signal to send to the server to kill it. (such as 2, 15, 9 or 'stop')
        :param port: The port the server will run on.
        :param max_ram: The maximum amount of RAM the server can use.
        :param max_cpu: The maximum amount of CPU the server is allowed to use. (eg, 50% of the CPU's max capacity)
        :param max_storage: The maximum amount of storage the server can use.
        :param hostname: The hostname of the server. (default is 0.0.0.0)
        :return bool: True if the server was created successfully, False if it was not.
        '''
        thorns.validate_data(thorns.compile_data_from_func())

        # Determines a 'Server Unique ID'. Identifier is the name of the server.
        alphabet_numbers = 'abcdefghijklmnopqrstuvwxyz0123456789'
        ServerUniqueID = None
        # Assures ID IS unique
        while os.path.exists(f'servers/{ServerUniqueID}') is True or ServerUniqueID is None:
            ServerUniqueID = ''.join(random.choice(alphabet_numbers) for _ in range(16))
            # Cuts down SUID to 8 characters
            ServerUniqueID = ServerUniqueID[:8]

            # Adds Prefix 'thorn_' to the SUID
            ServerUniqueID = f'thorn_{ServerUniqueID}'

        if thorns.check_exists(name_id=identifier) is True:
            raise thorns.errors.ServerExists(f"Server with the name '{identifier}' already exists.")

        assert not identifier.startswith('thorn_'), "the name id cannot start with 'thorn_'"

        # Creates the server data's template
        server = dt.SERVER_INSTANCE
        server['owner'] = owner_email
        server['identifier'] = identifier
        server['server_unique_id'] = ServerUniqueID
        server['description'] = description
        server['hostname'] = hostname
        server['port'] = port
        server['init_cmd'] = init_cmd
        server['install_cmds'] = install_cmds
        server['kill_signal'] = kill_signal
        server['online'] = False
        server['content_dir'] = os.path.abspath(f'servers/{ServerUniqueID}/content')
        server['resources']['RAM']['total'] = max_ram
        server['resources']['CPU']['allowed'] = max_cpu
        server['resources']['STORAGE']['total'] = max_storage

        logging.info(
            f"User '{owner_email}' created a new server with the identifier '{identifier}' ({ServerUniqueID})."
        )

        try:
            # Creates the directory where the data for the server is saved.
            os.makedirs(f'servers/{ServerUniqueID}', exist_ok=True)

            # Creates config file.
            var.fill_json(file=f'servers/{ServerUniqueID}/config.json', data=server)

            # Creates server content dir
            os.makedirs(server['content_dir'], exist_ok=True)
        except PermissionError as err:
            err_msg = f"PERMISSION ERROR: The OS is stopping us from accessing 'servers/{ServerUniqueID}' Please fix this."
            print(err_msg)
            logging.error(
                message=err_msg,
                exception=err
            )
            return False

        # Attempts the install command.
        if len(server['install_cmds']) > 0:
            index_place = 0
            try:
                os.chdir(server['content_dir'])
                for cmd in server['install_cmds']:
                    subprocess.run(shlex.split(cmd))
                    index_place += 1
            except Exception as err:
                logging.error(
                    message=f"An error occurred while installing the server '{identifier}'.",
                    exception=err
                )
                # Returns the error and the index of the command that failed.
                return {'success':False, 'error':err, 'list_index': index_place}

        logging.info(f"Server '{identifier}' was created successfully.")
        return True

    def delete(identifier:str, senders_email:str) -> bool:
        thorns.validate_data(thorns.compile_data_from_func())

        if thorns.check_exists(name_id=identifier) is False:
            raise thorns.errors.ServerDoesNotExist(f"Server '{identifier}' does not exist.")
        suid = thorns.get_idtype_target(identifier, 'suid')

        # Deletes the server
        shutil.rmtree(f'servers/{suid}')

        logging.info(f"User '{senders_email}' deleted the server '{identifier}'.")
        return True

    def start(identifier, senders_email:str) -> multiprocessing.Queue:
        identifier = thorns.get_idtype_target(identifier, 'suid')
        if thorns.check_exists(suid=identifier) is False:
            raise thorns.errors.ServerDoesNotExist(f"Server '{identifier}' does not exist.")

        input_pipe = multiprocessing.Pipe()

        # Start the server
        assert identifier is not None, 'suid is None.'
        process = multiprocessing.Process(
            target=thorns.worker,
            args=(identifier, input_pipe, DEBUG),
            name=identifier
        )
        process.start()

        logging.info(f"User '{senders_email}' started the server '{identifier}'{' in debug mode' if DEBUG else ''}.")
        return input_pipe

    def stop(identifier:str, senders_email:str) -> bool:
        thorns.validate_data(thorns.compile_data_from_func())

        if thorns.check_exists(name_id=identifier) is False:
            raise thorns.errors.ServerDoesNotExist(f"Server '{identifier}' does not exist.")
        if not identifier.startswith('thorn_'):
            suid = thorns.get_opposite_id(name_id=identifier)
        else:
            suid = identifier

        server = dict(var.load_all(file=f'servers/{suid}/config.json', dt_default=dt.SERVER_INSTANCE))
        saved_code = server['kill_signal']

        subprocess_pid = server['process_pid']

        for killcode in [saved_code, signal.SIGINT, signal.SIGTERM, signal.SIGKILL]:
            try:
                os.kill(subprocess_pid, killcode)
                # Checks if its dead
                # TODO: Find reliable way to check if the process is dead.
            except Exception as err:
                logging.error(f"Something went wrong stopping {suid}.", exception=err)

        # Stop the server
        server['online'] = False
        server['process_pid'] = None

        # Update the config file
        var.set(key='process_pid', value=None, file=f'servers/{suid}/config.json', dt_default=dt.SERVER_INSTANCE)
        var.set(key='online', value=False, file=f'servers/{suid}/config.json', dt_default=dt.SERVER_INSTANCE)

        logging.info(f"User '{senders_email}' stopped the server '{identifier}'.")
        return True

if __name__ == "__main__":
    print("This file cannot be ran directly. Please import it.")
