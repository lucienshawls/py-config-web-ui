import sys
import threading
import traceback
from collections.abc import Callable
from datetime import datetime
from io import StringIO

BASE_OUTPUT_STREAM = sys.stdout
BASE_ERROR_STREAM = sys.stderr


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


class ThreadOutputStream:
    """
    A thread-safe output stream manager that routes writes and flushes to different streams based on the current thread.

    Attributes:
        base_stream (StringIO): The default output stream used when no specific stream is associated with the thread.
        streams (dict[str, StringIO]): A mapping of thread IDs to their dedicated output streams.
        streams_to_terminal (dict[str, bool]): A mapping indicating whether the thread-specific stream also writes to the terminal (base_stream).
        streams_lock (dict[str, threading.Lock]): Locks to ensure thread-safe operations for each thread-specific stream.
        shared_streams (dict[str, StringIO]): A mapping of thread IDs to shared output streams, used across threads.
        shared_streams_lock (dict[str, threading.Lock]): Locks to ensure thread-safe operations for shared streams.
        lock (threading.Lock): A general lock for operations involving the base_stream.

    Methods:
        add_stream(thread_id: str, stream: StringIO, lock: threading.Lock, to_terminal: bool) -> None:
            Add a thread-specific output stream.
        add_shared_stream(thread_id: str, shared_stream: StringIO, shared_lock: threading.Lock) -> None:
            Add a shared output stream for a thread.
        write(message: str) -> None:
            Write a message to the appropriate streams based on the current thread.
        flush() -> None:
            Flush the appropriate streams based on the current thread.
    """

    def __init__(self, base_stream: StringIO) -> None:
        """
        Initialize the ThreadOutputStream with a base stream.

        Args:
            base_stream (StringIO): The default output stream used when no specific stream is associated with the thread.
        """
        self.base_stream = base_stream

        self.streams: dict[str, StringIO] = {}
        self.streams_to_terminal: dict[str, bool] = {}
        self.streams_lock: dict[str, threading.Lock] = {}

        self.shared_streams: dict[str, StringIO] = {}
        self.shared_streams_lock: dict[str, threading.Lock] = {}

        self.lock = threading.Lock()

    def add_stream(
        self,
        thread_id: str,
        stream: StringIO,
        lock: threading.Lock = threading.Lock(),
        to_terminal: bool = False,
    ) -> None:
        """
        Add a thread-specific output stream.

        Args:
            thread_id (str): The ID of the thread to associate with this stream.
            stream (StringIO): The output stream for this thread.
            lock (threading.Lock, optional): A lock to ensure thread-safe operations for this stream. Defaults to a new lock.
            to_terminal (bool, optional): If True, writes to this stream will also write to the base stream. Defaults to False.
        """
        self.streams[thread_id] = stream
        self.streams_to_terminal[thread_id] = to_terminal
        self.streams_lock[thread_id] = lock

    def add_shared_stream(
        self,
        thread_id: str,
        shared_stream: StringIO,
        shared_lock: threading.Lock,
    ) -> None:
        """
        Add a shared output stream for a thread.

        Args:
            thread_id (str): The ID of the thread to associate with this shared stream.
            shared_stream (StringIO): The shared output stream for this thread.
            shared_lock (threading.Lock): A lock to ensure thread-safe operations for this shared stream. Defaults to a new lock.
        """
        self.shared_streams[thread_id] = shared_stream
        self.shared_streams_lock[thread_id] = shared_lock

    def write(self, message: str) -> None:
        """
        Write a message to the appropriate streams based on the current thread.

        The message is written to the thread-specific stream, and optionally to the terminal (base_stream) and shared streams.

        Args:
            message (str): The message to write.
        """
        thread_id = threading.current_thread().name
        stream = self.streams.get(thread_id, self.base_stream)
        lock = self.streams_lock.get(thread_id, self.lock)
        with lock:
            stream.write(message)
        if self.streams_to_terminal.get(thread_id, False):
            with self.lock:
                self.base_stream.write(message)
        shared_stream = self.shared_streams.get(thread_id, None)
        shared_lock = self.shared_streams_lock.get(thread_id, None)
        if (shared_stream is not None) and (shared_lock is not None):
            with shared_lock:
                shared_stream.write(message)

    def flush(self) -> None:
        """
        Flush the appropriate streams based on the current thread.

        The flush operation is applied to the thread-specific stream, and optionally to the terminal (base_stream) and shared streams.
        """
        thread_id = threading.current_thread().name
        stream = self.streams.get(thread_id, self.base_stream)
        lock = self.streams_lock.get(thread_id, self.lock)
        with lock:
            stream.flush()
        if self.streams_to_terminal.get(thread_id, False):
            with self.lock:
                self.base_stream.flush()
        shared_stream = self.shared_streams.get(thread_id, None)
        shared_lock = self.shared_streams_lock.get(thread_id, None)
        if (shared_stream is not None) and (shared_lock is not None):
            with shared_lock:
                shared_stream.flush()


class ProgramRunner:
    """
    A class for managing the execution of a function in a separate thread while capturing
    its standard output and error streams. This allows for controlled execution, logging,
    and retrieval of results and output.

    Attributes:
        function (Callable): The function to be executed in a separate thread.
        hide_terminal_output (bool): Whether to hide standard output from the terminal.
        hide_terminal_error (bool): Whether to hide error output from the terminal.
        running (bool): Indicates if the function is currently running.
        warning_occurred (bool): Indicates if a warning occurred during execution.
        res (ResultStatus): Stores the result status of the executed function.
        io_out (StringIO): Captures standard output.
        io_err (StringIO): Captures standard error.
        io_combined (StringIO): Captures combined output of standard output and error.
        lock (threading.Lock): Ensures thread-safe access to shared attributes.
        output_lock (threading.Lock): Ensures thread-safe writes to the standard output stream.
        error_lock (threading.Lock): Ensures thread-safe writes to the error output stream.
        combined_output_lock (threading.Lock): Ensures thread-safe writes to the combined stream.

    Methods:
        capture_output():
            Captures and updates the output, error, and combined streams.
        run_in_separate_context(*args, **kwargs):
            Executes the target function in a separate thread while capturing output and handling exceptions.
        run(*args, **kwargs):
            Starts the function execution in a new thread.
        get_output(recent_only: bool = False) -> str:
            Retrieves the captured standard output.
        get_error(recent_only: bool = False) -> str:
            Retrieves the captured standard error.
        get_combined_output(recent_only: bool = False) -> str:
            Retrieves the captured combined output.
        get_res() -> ResultStatus:
            Retrieves the result status of the executed function.
        clear():
            Clears all captured output and resets result status.
        has_warning() -> bool:
            Checks if a warning occurred during execution.
        is_running() -> bool:
            Checks if the function is currently running.
        wait_for_join():
            Waits for the execution thread to complete.
    """

    def __init__(
        self,
        function: Callable,
        hide_terminal_output: bool = False,
        hide_terminal_error: bool = False,
    ) -> None:
        """
        Initializes the ProgramRunner with a target function and optional terminal output settings.

        Args:
            function (Callable): The function to be executed.
            hide_terminal_output (bool, optional): If True, suppress standard output in the terminal.
                Defaults to False.
            hide_terminal_error (bool, optional): If True, suppress standard error in the terminal.
                Defaults to False.

        Raises:
            TypeError: If the provided function is not callable.
        """
        if not callable(function):
            raise TypeError(
                f"function must be a callable function, not {type(function)}."
            )
        self.function = function

        self.running = False
        self.warning_occurred = False
        self.res = ResultStatus(True)

        self.io_out = StringIO()
        self.io_err = StringIO()
        self.io_combined = StringIO()

        self.hide_terminal_output = hide_terminal_output
        self.hide_terminal_error = hide_terminal_error

        self.lock = threading.Lock()
        self.output_lock = threading.Lock()
        self.error_lock = threading.Lock()
        self.combined_output_lock = threading.Lock()

        self.clear()

    def capture_output(self) -> None:
        """
        Captures and updates the standard output, error, and combined streams.

        If new data is present in the streams, it is cleared from the temporary buffers
        and appended to the permanent output storage.
        """
        if not self.running:
            return None
        with self.output_lock:
            new_out = self.io_out.getvalue()
            if new_out != "":
                self.io_out.truncate(0)
                self.io_out.seek(0)
        with self.error_lock:
            new_err = self.io_err.getvalue()
            if new_err != "":
                self.io_err.truncate(0)
                self.io_err.seek(0)
        with self.combined_output_lock:
            new_combined = self.io_combined.getvalue()
            if new_combined != "":
                self.io_combined.truncate(0)
                self.io_combined.seek(0)

        with self.lock:
            self.output += new_out
            self.recently_added_output += new_out

            self.error += new_err
            self.recently_added_error += new_err

            self.combined_output += new_combined
            self.recently_added_combined_output += new_combined

            if new_err != "":
                self.warning_occurred = True

    def run_in_separate_context(self, *args, **kwargs) -> None:
        """
        Executes the target function in a separate thread, capturing its output and handling exceptions.

        This method manages thread-local streams for capturing output and errors and updates
        the result status based on the function's return value or exceptions raised.

        Args:
            *args: Positional arguments for the target function.
            **kwargs: Keyword arguments for the target function.
        """
        thread_id = threading.current_thread().name
        try:
            assert isinstance(
                sys.stdout, ThreadOutputStream
            ), "Failed to hijack stdout."
            assert isinstance(
                sys.stderr, ThreadOutputStream
            ), "Failed to hijack stderr."
            sys.stdout.add_stream(
                thread_id=thread_id,
                stream=self.io_out,
                lock=self.output_lock,
                to_terminal=not self.hide_terminal_output,
            )
            sys.stdout.add_shared_stream(
                thread_id=thread_id,
                shared_stream=self.io_combined,
                shared_lock=self.combined_output_lock,
            )
            sys.stderr.add_stream(
                thread_id=thread_id,
                stream=self.io_err,
                lock=self.error_lock,
                to_terminal=not self.hide_terminal_error,
            )
            sys.stderr.add_shared_stream(
                thread_id=thread_id,
                shared_stream=self.io_combined,
                shared_lock=self.combined_output_lock,
            )

            formatted_time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f">_ [{formatted_time_now}]")
            res: ResultStatus | bool = self.function(*args, **kwargs)
            sys.stdout.flush()
            sys.stderr.flush()
            self.capture_output()
            with self.lock:
                if isinstance(res, ResultStatus):
                    self.res = res.copy()
                    if len(self.res.get_messages()) == 0:
                        self.res.add_message("Success.")
                elif isinstance(res, bool):
                    if not res:
                        self.res.set_status(False)
                        self.res.add_message("Failed.")
                    else:
                        self.res.add_message("Success.")
                else:
                    self.res.add_message("Success.")
            self.running = False

        except Exception as e:
            sys.stdout.flush()
            sys.stderr.flush()
            self.capture_output()
            with self.lock:
                self.res.set_status(False)
                self.res.add_message(
                    "".join(traceback.format_exception_only(type(e), e)).strip()
                )
                new_err = traceback.format_exc()
                self.error += new_err
                self.recently_added_error += new_err

                if not self.hide_terminal_error:
                    print(new_err, end="", file=BASE_ERROR_STREAM)
            self.running = False

    def run(self, *args, **kwargs) -> None:
        """
        Starts the function execution in a new thread.

        Args:
            *args: Positional arguments for the target function.
            **kwargs: Keyword arguments for the target function.

        Returns:
            ResultStatus: Indicates if the program was successfully started.
        """
        if hasattr(self, "program_thread") and self.program_thread.is_alive():
            return ResultStatus(False, "Program is already running.")

        self.running = True
        self.warning_occurred = False
        self.res = ResultStatus(True)
        self.program_thread = threading.Thread(
            target=self.run_in_separate_context, args=args, kwargs=kwargs
        )
        self.program_thread.start()
        return ResultStatus(True)

    def get_output(self, recent_only: bool = False) -> str:
        """
        Retrieves the captured standard output.

        Args:
            recent_only (bool, optional): If True, only returns the output
                added since the last retrieval. Defaults to False.

        Returns:
            str: The captured standard output.
        """
        self.capture_output()
        with self.lock:
            if bool(recent_only):
                output = self.recently_added_output
            else:
                output = self.output
            self.recently_added_output = ""
        return output

    def get_error(self, recent_only: bool = False) -> str:
        """
        Retrieves the captured error output. Since all the exceptions are
            captured, the error output usually contains only warnings.

        Args:
            recent_only (bool, optional): If True, only returns the error output
                added since the last retrieval. Defaults to False.

        Returns:
            str: The captured error output.
        """
        self.capture_output()
        with self.lock:
            if bool(recent_only):
                error = self.recently_added_error
            else:
                error = self.error
            self.recently_added_error = ""
        return error

    def get_combined_output(self, recent_only: bool = False) -> str:
        """
        Retrieves the captured combined output of standard and error streams.

        Args:
            recent_only (bool, optional): If True, only returns the combined output
                added since the last retrieval. Defaults to False.

        Returns:
            str: The captured combined output.
        """
        self.capture_output()
        with self.lock:
            if bool(recent_only):
                combined_output = self.recently_added_combined_output
            else:
                combined_output = self.combined_output
            self.recently_added_combined_output = ""
        return combined_output

    def get_res(self) -> ResultStatus:
        """
        Retrieves the result status of the executed function.

        Returns:
            ResultStatus: The current result status object, containing execution
            status, messages, and other relevant details.
        """
        with self.lock:
            return self.res

    def clear(self) -> None:
        """
        Resets all captured outputs, warnings, and execution status.

        This can only be performed when no function is running.
        """
        if self.is_running():
            return None
        with self.lock:
            self.output = ""
            self.recently_added_output = ""

            self.error = ""
            self.recently_added_error = ""

            self.combined_output = ""
            self.recently_added_combined_output = ""

            self.res = ResultStatus(True)
            self.warning_occurred = False

    def has_warning(self) -> bool:
        """
        Checks if any warnings were captured during execution.

        Returns:
            bool: True if warnings were captured, False otherwise.
        """
        with self.lock:
            return self.warning_occurred

    def is_running(self) -> bool:
        """
        Indicates whether the function is currently running.

        Returns:
            bool: True if the function is running, False otherwise.
        """
        with self.lock:
            return self.running

    def wait_for_join(self) -> None:
        """
        Waits for the function execution thread to complete.

        This method blocks the calling thread until the execution thread
        finishes.
        """
        if hasattr(self, "program_thread"):
            self.program_thread.join()
