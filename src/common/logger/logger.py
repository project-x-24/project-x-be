import functools
import logging
import sys
import time
import src.config as config


class DistributedLogger(object):
    _tag = ""
    _silent = False

    @property
    def logger(self):
        return self._logger

    @logger.setter
    def logger(self, logger):
        self._logger = logger

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, tag):
        self._tag = tag

    @property
    def silent(self):
        return self._silent

    @silent.setter
    def silent(self, silent):
        self._silent = silent

    def log(self, level, msg, *args, **kwargs):
        self._logger.log(level, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        msg = f"{self._tag}::{msg}"
        if not self._silent:
            self._logger.info(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        msg = f"{self._tag}::{msg}"
        if not self._silent:
            self._logger.debug(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        msg = f"{self._tag}::{msg}"
        if not self._silent:
            self._logger.error(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        msg = f"{self._tag}::{msg}"
        if not self._silent:
            self._logger.warning(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        msg = f"{self._tag}::{msg}"
        if not self._silent:
            self._logger.warning(msg, *args, **kwargs)


log_wrapper = DistributedLogger()


def get_formatter():
    formatter = "%(asctime)s — %(name)s — %(levelname)s — %(message)s"
    # formatter = "%(levelname)s — %(message)s"

    return formatter


def get_console_handler(formatter):
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(formatter))
    return console_handler


def get_logger(logger_name=None) -> DistributedLogger:
    root_logger = logging.getLogger(logger_name)
    root_logger.setLevel(logging.INFO)

    if not root_logger.handlers:
        formatter = get_formatter()
        root_logger.addHandler(get_console_handler(formatter))

        # with this pattern, it's rarely necessary to propagate the error up to parent
        root_logger.propagate = False

    log_wrapper.logger = root_logger
    return log_wrapper


def set_logger_tag(log_tag):
    log_wrapper.tag = log_tag


def set_logger_silent(log_silent):
    log_wrapper.silent = log_silent


def log_function_entry_and_exit(decorated_function):
    """
    Function decorator logging entry + exit and parameters of functions.

    Entry and exit as logging.info, parameters as logging.DEBUG.
    """

    @functools.wraps(decorated_function)
    def wrapper(*dec_fn_args, **dec_fn_kwargs):
        # Log function entry
        func_name = decorated_function.__qualname__
        name_dict = dict(func_name=func_name)
        logging.info(f">>> Entering function: {func_name}", extra=name_dict)

        # Execute wrapped (decorated) function:
        start_time = time.perf_counter()
        out = decorated_function(*dec_fn_args, **dec_fn_kwargs)
        end_time = time.perf_counter()

        logging.info(f"<<< Exiting function: {func_name}. Time taken: {end_time-start_time} secs", extra=name_dict)

        return out

    return wrapper
