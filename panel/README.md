# Thorns | Web Server
Thorns is a web server that is designed to be easy to use and setup. It is much like Apache or Nginx,<br>
currently, it runs out of the box.

This file will detail how to configure thorns to look how you want it to look.<br>

## Configuration
Thorns is configured via a `settings.json` file in the root directory of the project.<br>
It is also configurable via the CLI.<br>
The relevant settings are as follows:
- `group_logo_reldir` *(def: 'assets/img/icon.png')* str: The relative directory where the business logo is stored.<br>
- `group_name` *(def: 'Rose Panel')* str: The name of the group. (This could be your business, team, etc.)<br>
- `host_name` *(def: 'localhost')* str: The hostname of the API Server.<br>
- `port` *(def: 8000)* int: The port the API Server is running on.<br>