# Rose Panel
Rose is a Web-based panel which lets you manage
any application or service you have running on your server.

It is much like PufferPanel or Pterodactyl.<br>
But unlike PufferPanel, this will have many features<br>
And unlike Pterodactyl, this is intended to be much easier to use and setup.<br>

## Features and Qualities
- Easy to use and setup
- Web-based interface for ease-of-access
- A 'welcome' screen for easy setup
- RoseAPI for easy integration with other services
- User Management control
  - Fine-grained permissions
  - User FTPS access (planned)
  - Server-per-user setup. (see below)
  - User token/session management
- Start, stop, create and delete servers of any kind on the go.

## Dependencies
- Python 3.11 installed (3.11 or 3.10 only)<br>
Better if not done via windows store or any app store that locks the python installation
- Administrator permissions.
  - This is to bind ports lower than 1024 on linux
  - This is also because what perms needed is unknown, and not going to be looked into. Just run as admin/root.
- Recommended 2gb of RAM minimum.
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

You would enter a environment variable like this into the secrets.env file
```env
DEBUG=False
ASK_EXIT=True
WEB_PORT=80
```

## IN-DEVELOPMENT NOTICE
*This project is still in development and is not ready for production use.<br>
Security has not been tested and features are currently being built.<br>
What you see in features is what's planned for the moment AND what is present.*

**LICENSE**<br>
This project is licensed under the CC0 1.0 Universal License. See the LICENSE file for more information.