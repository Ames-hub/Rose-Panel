# Rose Panel
Rose is a Web-based panel which lets you manage
any application or service you have running on your server.

It is much like PufferPanel or Pterodactyl.<br>
But unlike PufferPanel, this will have many features<br>
And unlike Pterodactyl, this will be much easier to use and setup.<br>

## Features and Qualities
- Easy to use and setup
- Web-based interface for ease-of-access
- A 'welcome' script for easy setup
- And Many more are planned!

## Dependencies
- Python 3.11 installed<br>
Better if not done via windows store or any app store that locks the python installation
- Docker Engine<br>
- Permissions to run docker commands such as 'run', 'stop', 'start', 'restart' etc.
<br><br>*Dependencies are subject to change as the project develops.<br>As for now, they are expected dependencies.*

## Environment Variables
You can enter environment variables into a `secrets.env` file in the root directory of the project.<br>
Entering variables into the actual OS is not planned to be intentionally supported, but it'll likely work anyway.<br>
The following environment variables are supported:
- `DEBUG`, *(def: 'False')* bool: Enables extra logging and debugging features.
- `ASK_EXIT`, *(def: 'True')* bool: If set to 'True', the program will ask for confirmation before exiting.
Configuration of such is supported in the program itself, but env variables have been added for ease-of-access.
- `ONE_TOKEN_ACCOUNTS`, *(def: 'False')* bool: If set to 'True', the program will only allow one token per account<br>
Useful for security, but may be annoying for some users.
- `WEB_PORT`, *(def: 8000)* int: The port the panel webgui will run on.
- `CLEAR_SESSIONS_ON_EXIT`, *(def: 'True')* bool: If set to 'True', the program will log all users out on exit

## IN-DEVELOPMENT NOTICE
*This project is still in development and is not ready for production use.<br>
Security has not been tested and no features have currently been built.
What you see in features is what's planned for the moment.*

**LICENSE**<br>
This project is licensed under the CC0 1.0 Universal License. See the LICENSE file for more information.