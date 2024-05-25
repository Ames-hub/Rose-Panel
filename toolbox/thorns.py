from toolbox.storage import var, dt
from toolbox.pylog import pylog
import multiprocessing
import subprocess
import inspect
import random
import shlex
import os

logging = pylog('logs/rose_%TIMENOW%.log')
os.makedirs('servers', exist_ok=True)

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

    def get_id_type(identifier:str):
        if identifier.startswith('thorn_'):
            return 'suid'
        else:
            return 'name'

    # TODO: Fix and ensure this works. Don't know if command can be sent to the process.
    def worker(init_cmd, cmd_queue:multiprocessing.Queue, output_queue:multiprocessing.Queue, identifier) -> str:
        '''
        This function is used to run a command in a separate process in a certain directory. AKA The backbone of Thorns.

        :param init_cmd: The command to run.
        :param cmd_queue: The queue to put new commands in.
        :param output_queue: The queue to put the output in.
        :param identifier: The identifier of the server.
        :return rc: The return code of the process.
        :return process: The process object.
        '''
        if thorns.get_id_type(identifier) == 'name':
            identifier = thorns.get_opposite_id(name_id=identifier)
        os.chdir(var.get('content_dir', file=f'servers/{identifier}/config.json', dt_default=dt.SERVER_INSTANCE))
        process = subprocess.Popen(
            shlex.split(init_cmd),
            stdin=subprocess.PIPE,  # Allow writing to the subprocess
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        var.set('process_pid', process.pid, file=f'servers/{identifier}/config.json', dt_default=dt.SERVER_INSTANCE)

        while True:
            output = process.stdout.readline()
            # If the output is empty and the process has finished, break the loop.
            if process.poll() is not None: # If its not None, then its a return code. Indicating it has finished.
                break

            # If the output is not empty, put it in the queue.
            if output:
                output_queue.put(output.strip())

            # Sends the command to the process if the queue for commands is not empty.
            if not cmd_queue.empty():
                cmd = cmd_queue.get()
                if cmd is not str:
                    continue
                process.stdin.write(cmd + b'\n')
                process.stdin.flush()
        rc = process.poll()

        # Sets the server to offline and PID to None since the process is dead. (or should be)
        var.set('online', False, file=f'servers/{identifier}/config.json', dt_default=dt.SERVER_INSTANCE)

        # Tries to stop it, just incase it didn't die for some reason. prevents 'rogue programs'
        process_pid = var.get('process_pid', file=f'servers/{identifier}/config.json', dt_default=dt.SERVER_INSTANCE)
        try:
            thorns.stop(identifier, f'thorns.worker.{identifier}')
        except:
            pass
        var.set('process_pid', None, file=f'servers/{identifier}/config.json', dt_default=dt.SERVER_INSTANCE)
        var.set('worker_pid', None, file=f'servers/{identifier}/config.json', dt_default=dt.SERVER_INSTANCE)

        return rc # Return code.

    def create(identifier,
               description,
               owner_email,
               init_cmd,
               install_cmds:list,
               kill_signal,
               port=None,
               max_ram=1024, max_cpu=-1, max_storage=2048, # MiB and CPU is "allowed" percentage. -1 is unlimited.
               hostname="0.0.0.0") -> bool:
        '''
        Creates a new server instance.

        :param description: The description of the server.
        :param owner_email: The email of the person trying to make the server.
        :param init_cmd: The command to run to start the server. (such as "python3 main.py -O")
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

        # Creates the server data's template
        server = dt.SERVER_INSTANCE
        server['owner'] = owner_email
        server['identifier'] = identifier
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
                return {'success':False, 'error':err, 'list_index': index_place}

        return True

    def delete(identifier:str, senders_email:str):
        thorns.validate_data(thorns.compile_data_from_func())

        if thorns.check_exists(name_id=identifier) is False:
            raise thorns.errors.ServerDoesNotExist(f"Server '{identifier}' does not exist.")
        suid = thorns.get_opposite_id(name_id=identifier)

        # Deletes the server
        os.system(f"rm -rf servers/{suid}")

        logging.info(f"User '{senders_email}' deleted the server '{identifier}'.")

    def start(identifier, senders_email:str):
        thorns.validate_data(thorns.compile_data_from_func())

        if thorns.check_exists(name_id=identifier) is False:
            raise thorns.errors.ServerDoesNotExist(f"Server '{identifier}' does not exist.")
        suid = thorns.get_opposite_id(name_id=identifier)

        server = dict(var.load_all(file=f'servers/{suid}/config.json', dt_default=dt.SERVER_INSTANCE))

        # Create a Queue for communication
        cmd_queue = multiprocessing.Queue()
        output_queue = multiprocessing.Queue()

        # Start the server
        process = multiprocessing.Process(
            name=suid, target=thorns.worker, args=(server['init_cmd'], cmd_queue, output_queue)
        )
        process.start()
        server['online'] = True
        server['worker_pid'] = process.pid

        # Update the config file
        var.set(key='worker_pid', value=process.pid, file=f'servers/{identifier}/config.json', dt_default=dt.SERVER_INSTANCE)
        var.set(key='online', value=True, file=f'servers/{identifier}/config.json', dt_default=dt.SERVER_INSTANCE)

        return True

    def stop(identifier:str, senders_email:str):
        thorns.validate_data(thorns.compile_data_from_func())

        if thorns.check_exists(name_id=identifier) is False:
            raise thorns.errors.ServerDoesNotExist(f"Server '{identifier}' does not exist.")
        if not identifier.startswith('thorn_'):
            suid = thorns.get_opposite_id(name_id=identifier)
        else:
            suid = identifier

        server = dict(var.load_all(file=f'servers/{suid}/config.json', dt_default=dt.SERVER_INSTANCE))
        saved_code = server['kill_signal']

        worker_pid = server['worker_pid']
        mp_process_pid = server['process_pid']
        for killcode in [saved_code, 15, 9]:
            try:
                os.kill(worker_pid, killcode)
                # Checks if its dead
                if os.waitpid(worker_pid, os.WNOHANG) == (0, 0):
                    break
            except Exception as err:
                if os.waitpid(worker_pid, os.WNOHANG) == (0, 0):
                    break
                logging.error(f"Something went wrong stopping {suid}.", exception=err)

        for killcode in [2, 15, 9]:
            try:
                os.kill(mp_process_pid, killcode)
                # Checks if its dead
                if os.waitpid(mp_process_pid, os.WNOHANG) == (0, 0):
                    break
            except Exception as err:
                if os.waitpid(mp_process_pid, os.WNOHANG) == (0, 0):
                    break
                logging.error(f"Something went wrong stopping {suid}.", exception=err)
        else:
            # If it does not break here, then the process is still alive and goes to 'else'
            # Probs wont work, but its worth a shot.
            thorns.find_process(suid).kill()

        # Stop the server
        server['online'] = False
        server['worker_pid'] = None
        server['process_pid'] = None

        # Update the config file
        var.set(key='worker_pid', value=None, file=f'servers/{suid}/config.json', dt_default=dt.SERVER_INSTANCE)
        var.set(key='process_pid', value=None, file=f'servers/{suid}/config.json', dt_default=dt.SERVER_INSTANCE)
        var.set(key='online', value=False, file=f'servers/{suid}/config.json', dt_default=dt.SERVER_INSTANCE)

    def find_process(name) -> multiprocessing.Process:
        # Returns the MP Child with the name
        for child in multiprocessing.active_children():
            if child.name == name:
                return child

if __name__ == "__main__":
    print("This file cannot be ran directly. Please import it.")
