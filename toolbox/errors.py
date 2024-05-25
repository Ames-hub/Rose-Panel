class error:
    class AccountNotFound(Exception):
        def __init__(self, email_address):
            self.email_address = email_address
            super().__init__(self.email_address)

        def __str__(self):
            return f"Account '{self.email_address}' not found."

    class AccountAlreadyExists(Exception):
        def __init__(self, email_address):
            self.email_address = email_address
            super().__init__(self.email_address)

        def __str__(self):
            return f"Account '{self.email_address}' already exists."

    class InvalidCredentials(Exception):
        def __init__(self, email_address, password):
            self.email_address = email_address
            self.password = password
            super().__init__(self.email_address, self.password)

        def __str__(self):
            return f"Invalid credentials for the account '{self.email_address}'."

    class InvalidToken(Exception):
        def __init__(self, token):
            self.token = token
            super().__init__(self.token)

        def __str__(self):
            return "Token does not exist or expired"

    class MissingRequiredFields(Exception):
        def __init__(self, fields:list):
            self.fields = fields
            super().__init__(self.fields)

        def __str__(self):
            return f"Missing required fields: {', '.join(self.fields)}"

    class TooManyFields(Exception):
        def __init__(self, fields:list):
            self.fields = fields
            super().__init__(self.fields)

        def __str__(self):
            return f"Too many fields provided: {', '.join(self.fields)}"

    class InsufficientPermissions(Exception):
        def __init__(self, permission):
            self.permission = permission
            super().__init__(self.permission)

        def __str__(self):
            return f"Insufficient permissions."

    class exited_question(Exception):
        def __init__(self):
            super().__init__()

        def __str__(self):
            return "User exited the question."
