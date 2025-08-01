class ResultStatus:
    """
    A class to store the status and messages of a result.

    Attributes:
        status (bool): The status of the result (True for success, False for failure).
        messages (list): A list of messages to describe the result.

    Methods:
        set_status(status: bool) -> None: Set the status of the result.
        get_status() -> bool: Get the status of the result.
        add_message(message: str) -> None: Add a message to the result.
        get_messages() -> list: Get the list of messages.
        copy() -> ResultStatus: Create a copy of the ResultStatus object.
        __bool__() -> bool: Get the status of the result.
        __repr__() -> str: Get the representation of the ResultStatus object.
        __str__() -> str: Get the string representation of the ResultStatus object.

    """

    def __init__(self, status: bool, message: list[str] | str | None = None) -> None:
        """
        Initialize the ResultStatus instance.

        Args:
            status (bool): The status of the result (True for success, False for failure).
            message (list[str] | str | None, optional): An optional message or list of messages. Defaults to None.

        Raises:
            TypeError: If `message` is neither a string, a list of strings, nor None.
        """
        self.set_status(status)
        self.messages = []
        if message is None:
            return
        if isinstance(message, list):
            for m in message:
                self.add_message(str(m))
        elif isinstance(message, str):
            self.add_message(message)
        else:
            raise TypeError(
                f"message must be a string or a list of strings, not {type(message)}."
            )

    def set_status(self, status: bool) -> None:
        """Set the status of the result."""
        self.status = bool(status)

    def get_status(self) -> bool:
        """Get the status of the result."""
        return self.status

    def add_message(self, message: str) -> None:
        """Add a message to the result."""
        self.messages.append(str(message))

    def get_messages(self) -> list[str]:
        """Get the list of messages."""
        return self.messages

    def copy(self) -> "ResultStatus":
        """
        Create a copy of the ResultStatus object.

        Returns:
            ResultStatus: A new instance with the same status and messages.
        """
        res = ResultStatus(self.status)
        for message in self.messages:
            res.add_message(message)
        return res

    def __bool__(self) -> bool:
        """Return the status of the result as a boolean."""
        return self.status

    def __repr__(self) -> str:
        """
        Get a detailed representation of the ResultStatus object.

        Returns:
            str: A detailed representation for debugging.
        """
        if len(self.messages) == 0:
            return f"ResultStatus(status={self.status}, messages=[])"
        else:
            formatted_messages = ",\n\t".join(self.messages)
            return f"ResultStatus(status={self.status}, messages=[\n\t{formatted_messages}\n])"

    def __str__(self) -> str:
        """
        Get a user-friendly string representation of the ResultStatus object.

        Returns:
            str: A user-friendly representation.
        """
        if len(self.messages) == 0:
            return f'Current status: {"Success" if self.status else "Fail"}, Messages: (No messages).\n'
        else:
            formatted_messages = ",\n\t".join(self.messages)
            return f'Current status: {"Success" if self.status else "Fail"}, Messages:\n\t{formatted_messages}\n'
