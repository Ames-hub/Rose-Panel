from toolbox.storage import var, settings_path, dt
from toolbox.pylog import pylog, logman
from toolbox.webserver import webserver
from difflib import get_close_matches
from toolbox.security import security
from toolbox.RoseApi import rose_api
from toolbox.thorns import thorns
from toolbox.errors import error
import multiprocessing
import platform
import datetime
import dotenv
import random
import json
import time
import os

dotenv.load_dotenv(dotenv_path="secrets.env")
DEBUG = os.environ.get('DEBUG', False) == 'True'

cmds_dict = {
    "help": {
        'msg': "List all commands.",
        'args': [],
    },
    "exit": {
        'msg': "Exit the program.",
        'args': [],
    },
    "cls": {
        'msg': "Clear the screen.",
        'args': [],
    },
    "clear": {
        'msg': "Clear the screen.",
        'args': [],
    },
    "panel": {
        'msg': "Manage the panel.",
        'args': ['stop', 'start'],
    },
    "sessions": {
        'msg': "Manage active sessions.",
        'args': ['list'],
    },
    # TODO: Implement delete arg
    "server": {
        'msg': "Manage and interact with servers.",
        'args': ['create', 'delete', 'list', 'start', 'stop'],
    },
}

colours = {
    # Gives colours that can be used for strings
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "purple": "\033[95m",
    "gray": "\033[90m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "black": "\033[30m",
    "reset": "\033[0m"
}

logging = pylog("logs/rose_%TIMENOW%.log")

class rose:
    def cli():
        '''
        Handles the command line interface. Not only that, but it is also useful for development to
        make functions available and callable BEFORE designing their web interface.
        :return:
        '''
        executing_similar = (False, None, None)
        logging.info("Rose Panel CLI has been called.")
        try:
            run_success = False
            # Captures current terminal text and puts it in a variable
            rose.clear_terminal()

            while True:
                if not executing_similar[0]:
                    print("Welcome to the RosePanel CLI.")
                    print("Type 'help' for a list of commands.")
                    cmd = input(f"{colours['green']}RosePanel{colours['reset']}> ").lower()
                    args = cmd.split(" ")[1:]
                    cmd = cmd.split(" ")[0]
                else:
                    cmd = executing_similar[1]
                    args = executing_similar[2]
                    executing_similar = (False, None, None)

                if DEBUG == 'True':
                    logging.debug(f'User input: {cmd}')
                    logging.debug(f'Arguments: {args}')

                max_args_possible = 1 # No arguments implemented yet.
                # If there are no args, pad the list with None.
                if len(args) == 0:
                    args = [None] * max_args_possible

                if len(args) > max_args_possible:
                    print(f"{colours['red']}Error: Too many arguments.{colours['reset']}")
                    continue

                if cmd == "":
                    run_success = True # Do nothing if the user just presses enter.
                if cmd == "debug":
                    print("DEBUG VALUES:")
                    print(f"DEBUG: {DEBUG}")
                    print(f"Operating System: {platform.platform()}")
                    print(f"Python Version: {platform.python_version()}")
                    run_success = True
                elif cmd == "help":
                    rose.list_commands()
                    try:
                        input("Enter any key to continue...")
                    except KeyboardInterrupt:
                        pass
                    run_success = True
                elif cmd in ["exit", "close", "stop"]:
                    print(f"{colours['red']}Are you sure you want to terminate Rose Panel? (y/n){colours['reset']}")
                    # Don't handle keyboard interrupts so that if the user CTRL+C's to escape faster, its not blocked.
                    if bool(os.environ.get('ASK_EXIT', True)) is True:
                        response = input().lower()
                        if response in ['n', 'no']:
                            print("Shutdown cancelled.")
                            continue
                    raise KeyboardInterrupt
                elif cmd == 'cls' or cmd == 'clear':
                    rose.clear_terminal()
                    run_success = True
                elif cmd == 'panel':
                    if len(args) == 0:
                        print('Invalid usage. Usage: panel <command>')
                        print('Commands')
                        print('- panel start\n- panel stop')

                    webpanel = rose.find_process("webgui")

                    if args[0] == 'start':
                        print('Starting panel...')
                        if webpanel is None:
                            ROSE_GUI = multiprocessing.Process(
                                target=webserver.main,
                                name="webgui",
                                args=(False, "panel")
                            )
                            ROSE_GUI.start()
                        run_success = True
                    elif args[0] == 'stop':
                        print('Stopping panel...')
                        if webpanel is not None:
                            try:
                                rose.kill_process("webgui")
                            except PermissionError:
                                print(f"{colours['red']}Failed to stop the panel due to a perms error. Try rebooting{colours['reset']}")
                        run_success = True
                    else:
                        run_success = False
                elif cmd == 'server':
                    if args[0] is None:
                        print('Invalid usage. Usage: server <command>')
                        print('Commands')
                        print('- server create\n- server delete\n- server list\n- server start\n- server stop\n- server restart')
                        run_success = True

                    root_user = dict(var.get(f'accounts//{var.get("root_email")}'))
                    try:
                        root_user = security.account(
                            email_address=root_user.get('email_address', None),
                            password=root_user.get('password', None)
                        )
                    except (error.AccountNotFound, error.InvalidCredentials) as err:
                        print(f"{colours['red']}Critical Error: {err}.{colours['reset']}")
                        print(f"Does account '{root_user.get('email_address', 'Undefined')}' exist with a valid password?")
                        continue
                    if args[0] == 'create':
                        def is_number(x):
                            try:
                                int(x)
                                return True
                            except:
                                return False

                        if DEBUG is False:
                            try:
                                identifier = rose.ask_question("What do you want to name the server?", filter_func=lambda x: x != '' and x is not None)
                                description = rose.ask_question("How would you describe the server?", filter_func=lambda x: x != '' and x is not None)
                                init_cmd = rose.ask_question("Enter the command to start the server.", filter_func=lambda x: x != '' and x is not None)
                                install_cmds = rose.ask_question("Enter the commands to install the server.", filter_func=lambda x: x != '' and x is not None,do_listing=True)
                                kill_signal = rose.ask_question("Enter the kill signal for the server.", filter_func=lambda x: x != '' and x is not None)
                                hostname = rose.ask_question("Enter the hostname.", default='0.0.0.0', filter_func=lambda x: x != '' and x is not None)
                                if rose.ask_question("Do you need a port opened? (y/*n)", filter_func=lambda x: x in ['y', 'yes']) in ['y', 'yes']:
                                    port = rose.ask_question("Enter the port number.", filter_func=is_number, default=random.randint(1000, 9999))
                                else:
                                    print("Going portless mode for this server.")
                                    port = None
                            except error.exited_question:
                                print("Exiting server creation...")
                                continue
                        else:
                            # Sets test data
                            identifier = "test MC server"
                            description = "A test MC Server"  # Minecraft vanilla server
                            init_cmd = f"java -Xmx1024M -Xms1024M -jar minecraft_server.1.8.9.jar nogui"  # 1024mb ram
                            if os.name != 'nt':
                                # Installs 1.8.9 MC Server
                                install_cmds = [
                                    'wget https://launcher.mojang.com/v1/objects/b58b2ceb36e01bcd8dbf49c8fb66c55a9f0676cd/server.jar -O minecraft_server.1.8.9.jar']
                            else:
                                # Installs 1.8.9 MC Server. Uses curl for windows
                                install_cmds = [
                                    'curl -o minecraft_server.1.8.9.jar https://launcher.mojang.com/v1/objects/901f0b2b1ab24e4fa4970b6e03e8acb5b8e5ac9d/server.jar']
                            kill_signal = 'exit'
                            hostname = "0.0.0.0"  # All interfaces
                            if rose.ask_question("Do you need a port opened? (y/*n)") in ['y', 'yes']:
                                port = random.randint(1000, 9999)
                            else:
                                print("Going portless mode for this server.")
                                port = None

                        success = root_user.create_server(
                            identifier=identifier,
                            description=description,
                            init_cmd=init_cmd,
                            install_cmds=install_cmds,
                            kill_signal=kill_signal,
                            hostname=hostname,
                            port=port
                        )

                        if success is True:
                            print(f"{colours['green']}Server created successfully.{colours['reset']}")
                        elif success is False:
                            print(
                                f"{colours['yellow']}Error: Server creation failed. Does your server already exist?{colours['reset']}")
                        elif success is dict:
                            print(
                                f"{colours['red']}Error: Server creation failed on running install command.{colours['reset']}")
                            print(
                                f"Problem: {success['error']}. Problem occured on command number {success['list_index']}.")

                        run_success = True
                    elif args[0] == 'delete':
                        # TODO: Implement this
                        print("Delete server is not implemented yet.")
                        run_success = True
                    elif args[0] == 'list':
                        print("Listing servers...")
                        count = 0
                        users_servers = root_user.list_servers()
                        for server in users_servers:
                            server = var.load_all(f'servers/{server}/config.json')
                            count += 1
                            print(f"============ {count} ============")
                            print(f"Identifier: {server['identifier']}")
                            print(f"Description: {server['description']}")
                            print(f"Hostname: {server['hostname']}")
                            print(f"Port: {server['port']}")
                            print(f"Init Command: {server['init_cmd']}")
                            print(f"Install Commands: {', '.join(server['install_cmds'])}")
                            print(f"Kill Signal: {server['kill_signal']}")
                        run_success = True
                    elif args[0] == 'stop':
                        while True:
                            print("Please enter the server you wish to stop. (Case sensitive)")
                            count = 0
                            users_servers = root_user.list_servers()
                            number_server_crossref = {}
                            valid_server_ids = []
                            for server in users_servers:
                                count += 1
                                server_id = thorns.get_opposite_id(server)
                                valid_server_ids.append(server_id)
                                number_server_crossref[count] = server_id
                                print(f"ID {count}: {server_id}")

                            while True:
                                target_server = rose.ask_question("Enter the server ID to stop.")
                                if target_server in number_server_crossref.keys():
                                    break
                                elif target_server in valid_server_ids:
                                    break
                                else:
                                    print("Invalid server ID. Please try again.")

                            root_user.stop_server(server_id=target_server)
                    elif args[0] == 'start':
                        while True:
                            print("Please enter the server you wish to start. (Case sensitive)")
                            count = 0
                            users_servers = root_user.list_servers()
                            number_server_crossref = {}
                            valid_server_ids = []
                            for server in users_servers:
                                count += 1
                                server_id = thorns.get_opposite_id(server)
                                valid_server_ids.append(server_id)
                                number_server_crossref[count] = server_id
                                print(f"ID {count}: {server_id}")

                            # TODO: Fix this not starting servers
                            while True:
                                target_server = rose.ask_question("Enter the server ID to start.")
                                if target_server in number_server_crossref.keys():
                                    break
                                elif target_server in valid_server_ids:
                                    break
                                else:
                                    print("Invalid server ID. Please try again.")

                            root_user.start_server(server_id=target_server)

                elif cmd == 'sessions':
                    if len(args) == 0:
                        print('Invalid usage. Usage: sessions <command>')
                        print('Commands')
                        print('- sessions list')
                        run_success = True
                    elif args[0] == 'list':
                        sessions = dict(var.get('tokens'))
                        if sessions == {}:
                            print("No sessions found.")
                            continue

                        print('Listing sessions...')
                        iterance = 0
                        for token in sessions.keys():
                            iterance += 1
                            session = sessions[token]
                            print(f"============ {iterance} =============")
                            print(f"Token: {token}")
                            print(f"Owner: {session['belongs_to']}")
                            print(f"Expires: {datetime.datetime.fromtimestamp(session['expire_on'])}")
                        # Wraps up the session in the appropriate formatting.
                        print("=========================")
                        run_success = True
                elif cmd in ["uwu", 'owo']: # lol
                    print("owo" if cmd == "uwu" else "owo")
                    time.sleep(1)

                if not run_success:
                    # Acts as an Else block. If a sub-command is not found, will now fall here.
                    print(f"{colours['red']}Error: Command not found.{colours['reset']}")
                    similar = rose.find_similar(cmd, ask_to_execute=True, cmd_args=args)
                    if similar is not None:
                        executing_similar = (True, similar['cmd'], similar['args'])
                        continue
                run_success = False # Set back to false for the next command.
                executing_similar = (False, None, None) # Reset the tuple just in case.
        except KeyboardInterrupt:
            rose.shutdown()

    def ask_question(
            question:str,
            options:list=None,
            exit_phrase='exit',
            confirm_validity=True,
            show_default=True,
            default=None,
            filter_func=None,
            colour='green',
            do_listing:bool=False
            ) -> str:
        """
        Prompts the user with a question and returns their response.

        This function will keep asking the question until a valid response is given.
        A response is considered valid if it is included in the options list (if provided)
        and if it passes the filter function (if provided).

        :param question: (str) The question to ask the user.
        :param options: (list, optional) A list of valid responses. If None, all responses are considered valid. Defaults to None.
        :param exit_phrase: (str, optional) A phrase that, if inputted, will raise an 'exited_question' error. Defaults to 'exit'.
        :param confirm_validity: If True, the user will be asked to confirm their response.
        :param show_default: If True, the default value will be shown in the prompt.
        :param default: (any, optional) A default value to return if a KeyboardInterrupt is raised. Defaults to None.
        :param filter_func: (callable, optional) A function that takes the user's response as input and returns a boolean
        :param colour: (str, optional) The colour of the prompt. Defaults to 'green'.
        :param do_listing: (bool, optional) If True, the user must input a list of responses. Defaults to False.

        example filter_func:

        >>> def filter_func(question_answer):
        >>>     return question_answer >= 0

        Lambda functions can also be used.

        Returns:
        str: The user's response.

        Raises:
        error.exited_question: If the user inputs the 'exit_phrase'.
        """
        assert do_listing in [True, False], "Do_listing must be a boolean."
        try:
            answers_list = [] # Not used unless get_type is list.
            while True:
                print(question if not show_default else f"{question} || Default: {default}")
                if do_listing is True:
                    print("(Type 'done' to finish giving answers)")
                    # Gets an answer, tells user how many answers they have given.
                    response = input(f"({len(answers_list)}) {colours[colour]}>>> {colours['reset']}")
                    if response == '':
                        print(f"{colours['red']}Error: Invalid response. Cannot choose default for lists.{colours['reset']}")
                        continue
                    if response == exit_phrase:
                        raise error.exited_question

                    try:
                        if not filter_func(response):
                            print(f"{colours['red']}Error: response breaks requirement rules.{colours['reset']}")
                            continue
                    except Exception as err:
                        logging.error(f"Error in filter function: {err}", exception=err)
                        print("Error while trying to run data validation filters. Do you want to continue? (y/*n)")
                        retry = input(f"{colours['red']}>>> {colours['reset']}").lower()
                        if retry not in ['y', 'yes']:
                            raise error.exited_question

                    answers_list.append(response)
                    if response != 'done':
                        continue
                else:
                    response = input(f"{colours[colour]}>>> {colours['reset']}")

                if exit_phrase == response:
                    raise error.exited_question
                elif response == '':
                    response = default

                if options is not None:
                    if response not in options:
                        print(f"{colours['red']}Error: Invalid response.{colours['reset']}")
                        continue

                if filter_func is not None:
                    try:
                        if not filter_func(response):
                            print(f"{colours['red']}Error: response breaks requirement rules.{colours['reset']}")
                            continue
                    except Exception as err:
                        logging.error(f"Error in filter function: {err}", exception=err)
                        print("Error while trying to run data validation filters. Do you want to continue? (y/*n)")
                        retry = input(f"{colours['red']}>>> {colours['reset']}").lower()
                        if retry not in ['y', 'yes']:
                            raise error.exited_question

                if confirm_validity:
                    if response != default:
                        print("Is that correct? (y/*n)")
                    else:
                        print("use the default? (*y/n)")
                    valid = input().lower()
                    if valid not in ['y', 'yes']:
                        continue

                return response
        except KeyboardInterrupt:
            return default

    def clear_terminal():
        print(
            "Attempting to clear the screen... (this may not work on all systems. So we printed 100 lines to simulate a clear screen.)")
        for i in range(100):
            print('\n')
        os.system('cls' if os.name == 'nt' else 'clear')

    def shutdown():
        # Handles exiting the program.
        print(f"{colours['green']}Exiting Rose Panel.{colours['reset']}")
        print(f"{colours['red']}Please wait while we clean up...{colours['reset']}")

        # Chances are the processes will shutdown themselves, but we'll do it anyway. Just in case.
        for process in multiprocessing.active_children():
            pid = process.pid

            # Handle the program not running.
            if pid is None:
                continue

            try:
                os.kill(pid, 2)
            except PermissionError:
                try:
                    os.kill(pid, 9)
                except PermissionError:
                    # We can't do anything about it.
                    continue

        if os.environ.get('CLEAR_SESSIONS_ON_EXIT', True):
            # Clear the sessions.
            accounts_dict = dict(var.get('accounts'))
            for user in accounts_dict:
                accounts_dict[user]['current_session'] = None
            # Save the changes.
            var.set(f'accounts', accounts_dict, file=settings_path)
            # Clear the tokens.
            var.set('tokens', {}, file=settings_path)

        print(f"{colours['green']}Thank you. Goodbye!{colours['reset']}")

    def find_process(name) -> multiprocessing.Process or None:
        '''
        Finds a process by its name.
        :arg name: The name of the process to find.
        :return The process if found, otherwise None.
        '''
        return next((process for process in multiprocessing.active_children() if process.name == name), None)

    def kill_process(name):
        '''
        Kills a process by its name.
        :arg name: The name of the process to kill.
        '''
        process = rose.find_process(name)
        if process is not None:
            try:
                os.kill(process.pid, 2)
            except PermissionError:
                # Don't handle this permission error if it fails. Let it propagate up so it can be handled.
                os.kill(process.pid, 9)
        else:
            logging.warning(f'Failed to find program "{name}".')

    def list_commands(return_only=False) -> dict:
        '''
        Lists all commands that the user can use in the CLI.

        :param return_only: If True, returns the dictionary of commands.
        :return: The dictionary of commands.
        '''
        if return_only:
            return cmds_dict
        else:
            for cmd, desc in cmds_dict.items():
                args_msg = ""
                cmd_has_args = desc['args']
                if cmd_has_args is not []:
                    args_msg = f"\nArguments: {', '.join(desc['args'])}"
                print(f"- {cmd}: {desc['msg']}\n{args_msg}")
            return cmds_dict

    def session_token_killer():
        '''
        Intended to be ran in a thread.
        Looks over sessions for their expiry date and deletes them if they are expired.
        '''
        old_sessions = None

        while True:
            # Get all the sessions
            sessions = dict(var.get('tokens'))
            try:
                for token in sessions.keys():
                    session = sessions[token]
                    if session['expire_on'] < datetime.datetime.now().timestamp():
                        del sessions[token]
                        session_owner = session['belongs_to']
                        var.set(f'accounts//{session_owner}//current_session', None, file=settings_path)
                        var.delete(f'tokens//{token}', file=settings_path)
            except RuntimeError: # Handles the dictionary changing size during iteration.
                continue
            except KeyboardInterrupt:
                break

            # Do it all at once to prevent spamming the disk.
            try:
                var.set(f'tokens', sessions, file=settings_path)
            except json.JSONDecodeError:
                # If the file is empty, we can't decode it. So we just skip it.
                continue

            try:
                old_same = old_sessions == sessions
                time.sleep(15 if not old_same else 30) # If the sessions haven't changed, sleep for 60 seconds.

                # Buffers the old sessions from changing so that the wait time isnt longer if the sessions are changing.
                if not old_same and random.choice([True, False]):
                    old_sessions = sessions
            except KeyboardInterrupt:
                break
        return True

    def find_similar(cmd:str, cmd_args:list, ask_to_execute=False) -> dict:
        '''
        Finds commands and args that are similar to the one the user entered.
        Used to help the user if they mistype a command.

        :param cmd: The command to find similar commands to.
        :param ask_to_execute: If True, asks the user if they want to execute the similar command or not.
        :param cmd_args: The arguments of the command.
        :return: The list of similar commands or None if the user doesn't want to execute them or there are no similar commands.
        '''
        try:
            similar_cmd = get_close_matches(
                word=cmd,
                possibilities=cmds_dict.keys(),
            )[0]
        except IndexError:
            return None

        if cmd_args[0] is not None:
            possible_args = cmds_dict[similar_cmd]['args']
            similar_args = []
            for i in range(len(cmd_args)):
                # Finds the similar args for the similar command.
                try:
                    similar_args.append(get_close_matches(
                        word=cmd_args[i],
                        possibilities=possible_args
                    )[0])
                except IndexError:
                    continue

            cmd_args = similar_args

        logging.info(f'User entered an invalid command: \"{cmd}\". (ask if should execute: {ask_to_execute}) Found similar command: \"{similar_cmd}\".')
        if not ask_to_execute:
            return {'cmd':similar_cmd, 'args':cmd_args}
        else:
            try:
                facsimile_cmd = f"{similar_cmd} {' '.join(cmd_args)}".strip()
            except TypeError:
                facsimile_cmd = similar_cmd # just use the command. (cmd args are None on type error)
            print(f"{colours['yellow']}Did you mean{colours['white']}: {colours['green']}\"{facsimile_cmd}\"? {colours['reset']}(*y/n)")
            response = input('>>> ').lower()
            if response not in ['n', 'no']:
                logging.info(f'User chose to execute the similar command: \"{similar_cmd}\".')
                return {'cmd':similar_cmd, 'args':cmd_args}
            else:
                logging.info(f'User did not execute the similar command: \"{similar_cmd}\".')
                return None

    def welcome_cli():
        '''
        A CLI that is used for when the user first starts the program.
        '''
        logging.info("Rose Panel has started its welcoming CLI function.")
        print(f"{colours['green']}Welcome to the RosePanel CLI.")

        # Create the config file
        if not os.path.exists(settings_path):
            with open(settings_path, 'w+') as f:
                json.dump(dt.SETTINGS, f, indent=4)

        print(f"{colours['reset']}We need to ask you some questions before we can continue.")

        # Gets the user's email address
        while True:
            print("Please enter your email address for the admin account.")
            email_address = input(f"{colours['red']}>>> {colours['reset']}")
            if '@' not in email_address:
                print(f"{colours['red']}Error: Invalid email address.{colours['reset']}")
                continue

            # Checks if it is the intended email address.
            if input(f"Is that correct? (*y/n)\n{colours['green']}>>> {colours['reset']}").lower() in ['n', 'no']:
                continue
            break

        # Make a password for the admin account
        while True:
            print("Create an Admin password for the panel.")
            admin_password = input(f"{colours['red']}>>> {colours['reset']}")
            is_correct = input(f"Please enter that again.\n{colours['red']}>>> {colours['reset']}")
            if admin_password != is_correct:
                print(f"{colours['red']}Error: Passwords do not match.{colours['reset']}")
                continue
            break

        # Create the first account
        ROOT_USER = dt.ACCOUNT
        ROOT_USER['permissions'] = security.perms.parse_for_file([security.perms.ADMINISTRATOR])
        ROOT_USER['email_address'] = email_address
        ROOT_USER['password'] = admin_password

        var.set(f'accounts//{email_address}', ROOT_USER)
        print(f"{colours['green']}Admin account created.{colours['reset']}")
        print("\nTo login, enter the following details to the web panel when it is ready:")
        print(f"{colours['yellow']}Email: {email_address}")
        print(f"Password: {admin_password}{colours['reset']}")
        input("\nPress any key to continue...")

        var.set('root_email', email_address)

        rose.clear_terminal()
        print(f"{colours['green']}RosePanel CLI has finished its setup.{colours['reset']}")
        print("Thank you for choosing RosePanel!")
        time.sleep(4)

        var.set('first_start', False)
        return True

if __name__ == "__main__":
    if var.get('first_start'):
        rose.welcome_cli()

    ROSE_GUI = multiprocessing.Process(
        target=webserver.main,
        name="webgui",
        args=(False, "panel")
    )
    ROSE_GUI.start()

    ROSE_API = multiprocessing.Process(
        target=rose_api.run,
        name="roseapi"
    )
    ROSE_API.start()

    LOGMAN = multiprocessing.Process(
        target=logman,
        name="logman"
    )
    LOGMAN.start()

    SESSION_KILLER = multiprocessing.Process(
        target=rose.session_token_killer,
        name="sessionkiller"
    )
    SESSION_KILLER.start()

    # Logs debug information for debugging problems with the program in support tickets/servers.
    logging.debug("Rose Panel and Pylog has started.")
    logging.debug(f"GUI Process ID: {ROSE_GUI.pid}")
    logging.debug(f"API Process ID: {ROSE_API.pid}")
    logging.debug(f"Log Manager Process ID: {LOGMAN.pid}")
    logging.debug(f"Debug mode: {DEBUG}")
    logging.debug(f"Operating System: {platform.platform(aliased=False, terse=False)}")

    time.sleep(1.5) # Wait for the webserver to start.

    if os.environ.get('DO_CLI', True) is True:
        rose.cli()
