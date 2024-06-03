from toolbox.security import settings_path
from toolbox.errors import error
from toolbox.storage import var

class permissions:
    '''
    Uses bitwise operations to determine permissions.
    If you wish to add more permissions, add them to the class and increment the right-most value by 1.
    '''
    # Keep this up to date with the permissions in the class. Mainly used for error returns on the API
    dict = {
        1 << 0: "Administrator",
        1 << 1: "Manage Permissions",
        1 << 2: "Delete Servers",
        1 << 3: "Create Servers",
        1 << 4: "Edit Servers",
        1 << 5: "List any server",
        1 << 6: "List my servers"
    }

    # The closer to 0 the permission is, the more powerful it is.
    ADMINISTRATOR = 1 << 0 # result is 1
    MANAGE_PERMISSIONS = 1 << 1 # result is 2 and so on. Double the previous value always.
    DELETE_SERVERS = 1 << 2 # 4
    MAKE_SERVERS = 1 << 3 # 8
    EDIT_SERVERS = 1 << 4 # 16
    LIST_OTHERS_SERVERS = 1 << 5 # 32
    LIST_SERVERS = 1 << 6 # 64

    def get_name(permission_value:str) -> list:
        # If a single integer is passed, convert it to a list
        if isinstance(permission_value, int):
            permission_value = [permission_value]

        permission_names = []
        for value in permission_value:
            if value in permissions.dict:
                permission_names.append(permissions.dict[value])
            else:
                permission_names.append(f"UNKNOWN_PERMISSION({value})")
        return permission_names

    def get_number(permission_name) -> list:
        # Creates a reverse of permissions.dict. Makes values key, makes keys value.
        reverse_dict = {v: k for k, v in permissions.dict.items()}
        number = reverse_dict.get(permission_name)
        if number is None:
            raise ValueError(f"Permission {permission_name} not found.")
        return number

    def require(needed_perms: list, email_address: str) -> bool:
        '''Checks only if the user has the required permissions. Do not use this to check if a password is valid.'''
        # Check if the email is valid.
        if email_address not in dict(var.get('accounts')).keys():
            raise error.AccountNotFound(email_address)

        # Get the user's account perms
        acc_perms = permissions.load(email_address)
        if permissions.ADMINISTRATOR in acc_perms:
            return True

        # Check if the user has the required permissions.
        for needed_perm in needed_perms:
            if acc_perms[needed_perm] is False:
                raise error.InsufficientPermissions(needed_perm)

        return True

    def set(causes_email: str, effects_email: str, permission: int, value: bool) -> bool:
        '''
        Saves the permissions to the user's account.

        :param causes_email: The email address of the user causing the change.
        :param effects_email: The email address of the user whose permissions are being changed.
        :param permission: The permission to set.
        :param value: The value to set the permission to.
        :return: True if the permission was set successfully.
        '''
        assert isinstance(value, bool)
        # Checks if both accounts exist
        if causes_email not in dict(var.get('accounts')).keys():
            raise error.AccountNotFound(causes_email)
        # Checks if the user has the required permissions.
        if causes_email != 'RosePanel':
            permissions.require([permissions.MANAGE_PERMISSIONS], causes_email)

        # Checks if the user exists.
        if effects_email not in dict(var.get('accounts')).keys():
            raise error.AccountNotFound(effects_email)

        var.set(f'accounts//{effects_email}//permissions//{permission}', value, file=settings_path)
        return True

    def load(email_address: str) -> list:
        '''
        Loads the permissions of the user.

        :param email_address: The email address of the user to load the permissions of.
        :return: A list of permissions the user has.
        '''
        perms = dict(var.get(f'accounts//{email_address}//permissions', file=settings_path))
        # Converts each key to an int and not a string from the dict
        converted_perms = {int(k): v for k, v in perms.items()}
        return converted_perms

if __name__ == "__main__":
    print("Do not run this file directly.")
