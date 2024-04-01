import os

colours = {
    # Gives colours that can be used for strings
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "purple": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "black": "\033[30m",
    "reset": "\033[0m"
}

class rose:
    @staticmethod
    def cli():
        while True:
            print("Welcome to the RosePanel CLI.")
            print("Type 'help' for a list of commands.")
            cmd = input("RosePanel> ").lower()
            args = cmd.split(" ")[1:]

            max_args_possible = 1 # No arguments implemented yet.
            if len(args) > max_args_possible:
                print(f"{colours['red']}Error: Too many arguments.{colours['reset']}")
                continue

            if cmd == "":
                continue # Do nothing if the user just presses enter.
            elif cmd == "help":
                rose.list_commands()
            elif cmd == "exit":
                raise KeyboardInterrupt
            elif cmd == 'cls' or cmd == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
            elif cmd == 'panel':
                if len(args) == 0:
                    print('Invalid usage. Usage: panel <command>')
                    print('Commands')
                    print('- panel start\n- panel stop')
                elif args[0] == 'start':
                    print('Starting panel...')
                elif args[0] == 'stop':
                    print('Stopping panel...')
            else:
                print(f"{colours['red']}Error: Command not found.{colours['reset']}")

    def list_servers() -> dict:
        #
        return {
            "NONE": {
                "name": 'server1',
                "ip": '192.168.0.192'
            }
        }

    def list_commands(return_only=False):
        cmds_dict = {
            "help": "List all commands.",
            "exit": "Exit the program.",
            "cls": "Clear the screen.",
            "clear": "Clear the screen.",
            "panel": "Manage the panel.",
            "server": "Manage the servers."
        }
        if return_only:
            return cmds_dict
        else:
            for cmd, desc in cmds_dict.items():
                print(f"- {cmd}: {desc}")

if __name__ == "__main__":
    try:
        rose.cli()
    except KeyboardInterrupt:
        # Handles exiting the program.
        print(f"{colours['green']}Exiting Rose Panel.{colours['reset']}")
        print(f"{colours['red']}Please wait while we clean up...{colours['reset']}")
        print(f"{colours['green']}Thank you. Goodbye!{colours['reset']}")
