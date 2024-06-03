from toolbox.pylog import pylog
import re
import os

logging = pylog(filename='logs/rose_%TIMENOW%.log')
settings_path = os.path.join(os.getcwd(), 'settings.json')

def sanitize(input_string):
    """
    Sanitizes input by removing potentially harmful characters.

    :param input_string: The input string to sanitize.
    :return: The sanitized input string.
    """
    # Define a regular expression pattern to match potentially harmful characters
    pattern = re.compile(r'[^\w\s@.-]', re.UNICODE)

    # Use the pattern to replace any matches with an empty string
    sanitized_string = re.sub(pattern, '', input_string)

    return sanitized_string
