from toolbox.pylog import pylog
import json
import os

logging = pylog(os.path.abspath("logs/rose_%TIMENOW%.log"))

memory_file = 'memory.json'
settings_path = 'settings.json'
# The seperator used to split keys in the var class when you access like 'key1//key2//key3'
key_seperator = "//"

class dt:
    '''
    a list of variables that are Data Tables (DTs) or python dictionaries.
    Does not determine data
    '''
    ACCOUNT = {
        'permissions': {},
        'email_address': None, # The key should be the username, but it'll be stored here too for easy access.
        'password': None,
        'current_session': None,
    }

    SETTINGS = {
        'first_start': True,
        'token_lifespan': 3600 * 4,  # 4 hours
        'ask_to_exit': True,
        'one_token_accounts': True,
        'hostname': '0.0.0.0',
        'ports': {
            'web': 8000,
            'api': 5005,
        },
        'root_email': None, # typically the email of the root account made on welcome CLI func
        'accounts': {},
        'tokens': {},
    }

    TOKEN_DICT = {
        'activity': {},  # Logs for this session token
        'expire_on': None,
        'belongs_to': None
    }

    SERVER_INSTANCE = {
        'owner': None,
        'identifier': None,
        'description': None,
        'hostname': None,
        'port': None,
        'init_cmd': None,
        'install_cmds': None, # A list of all commands needed to install server
        'kill_signal': 2, # Default is SIGINT. Might be a string or an int.
        'online': False,
        'process_pid': None,
        'worker_pid': None,
        'content_dir': None,
        'resources': {
            'RAM': {'used': 0, 'total': None},
            'CPU': {'used': 0, 'allowed': None},
            'STORAGE': {'used': 0, 'total': None},
        }
    }

class var:
    def set(key, value, file=settings_path, dt_default=dt.SETTINGS) -> bool:
        '''
        Sets the value of a key in the memory file.

        :param key: The key to set the value of.
        :param value: The value to set the key to.
        :param file: The file to set the key in.
        :param dt_default: The default dictionary to fill a json file with if the file does not exist.
        :return:
        '''
        keys = str(key).split(key_seperator)
        file_dir = os.path.dirname(file)
        if file_dir == '':
            file_dir = os.getcwd()

        if os.path.exists(file) is False:
            os.makedirs(file_dir, exist_ok=True)
            with open(file, 'w+') as f:
                json.dump(dt_default, f, indent=4, separators=(',', ':'))

        with open(file, 'r+') as f:
            data = json.load(f)

        temp = data
        for k in keys[:-1]:
            if k not in temp:
                temp[k] = {}
            temp = temp[k]

        temp[keys[-1]] = value

        with open(file, 'w+') as f:
            json.dump(data, f, indent=4)

        return True

    def get(key, default=None, dt_default=dt.SETTINGS, file=settings_path) -> object:
        '''
        Gets the value of a key in the memory file.

        :param key: The key to get the value of.
        :param default: The default value to return if the key does not exist.
        :param dt_default: The default dictionary to fill a json file with if the file does not exist.
        :param file: The file to get the key from.
        Set to None if you want to raise an error if the file does not exist.
        '''
        keys = str(key).split(key_seperator)
        file_dir = os.path.dirname(file)
        if file_dir == '':
            file_dir = os.getcwd()

        if os.path.exists(file) is True:
            with open(file, 'r+') as f:
                data = dict(json.load(f))
        else:
            if dt_default is not None:
                os.makedirs(file_dir, exist_ok=True)
                with open(file, 'w+') as f:
                    json.dump(dt_default, f, indent=4, separators=(',', ':'))
            else:
                raise FileNotFoundError(f"file '{file}' does not exist.")

            with open(file, 'r+') as f:
                data = dict(json.load(f))

        temp = data
        try:
            for k in keys[:-1]:
                if k not in temp:
                    return default
                temp = temp[k]

            return temp[keys[-1]]
        except KeyError as err:
            logging.error(f"key '{key}' not found in file '{file}'.", err)
            raise KeyError(f"key '{key}' not found in file '{file}'.")

    def delete(key, file=settings_path, default=dt.SETTINGS):
        '''
        Delete a key.

        :param key: The key to delete.
        :param file: The file to delete the key from.
        :param default: The default dictionary to fill a json file with if the file does not exist.
        '''
        keys = str(key).split(key_seperator)
        file_dir = os.path.dirname(file)
        if file_dir == '':
            file_dir = os.getcwd()

        if os.path.exists(file) is True:
            with open(file, 'r+') as f:
                data = dict(json.load(f))
        else:
            if default is not None:
                os.makedirs(file_dir, exist_ok=True)
                with open(file, 'w+') as f:
                    json.dump(default, f, indent=4, separators=(',', ':'))
            else:
                raise FileNotFoundError(f"file '{file}' does not exist.")

            with open(file, 'r+') as f:
                data = dict(json.load(f))

        temp = data
        for k in keys[:-1]:
            if k not in temp:
                return False
            temp = temp[k]

        if keys[-1] in temp:
            del temp[keys[-1]]
            with open(file, 'w+') as f:
                json.dump(data, f, indent=4)
            return True
        else:
            return False

    def load_all(file=settings_path, dt_default={}) -> dict:
        '''
        Load all the keys in a file. Returns a dictionary with all the keys.
        :param file: The file to load all the keys from.
        :param dt_default:
        :return:
        '''
        os.makedirs(os.path.dirname(file), exist_ok=True)
        if not os.path.exists(file):
            with open(file, 'w+') as f:
                json.dump(dt_default, f, indent=4, separators=(',', ':'))

        with open(file, 'r+') as f:
            data = dict(json.load(f))

        return data

    def fill_json(file=settings_path, data=dt.SETTINGS):
        '''
        Fill a json file with a dictionary.
        :param file: The file to fill with data.
        :param data: The data to fill the file with.
        '''
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, 'w+') as f:
            json.dump(data, f, indent=4, separators=(',', ':'))

        return True