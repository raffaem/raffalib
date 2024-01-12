#!/usr/bin/env python3
# Copyright 2023 Raffaele Mancuso
# SPDX-License-Identifier: GPL-2.0-or-later

import logging
import sys
import os
import datetime
import pathlib
import traceback

class MultiLineFormatter(logging.Formatter):
    """
    Multi-line formatter for MyLogger's handlers (but console handler and file handler).
    See: https://stackoverflow.com/questions/58590731/how-to-indent-multiline-message-printed-by-python-logger
    """

    def get_header_length(self, record):
        """Get the header length of a given record."""
        return len(
            super().format(
                logging.LogRecord(
                    name=record.name,
                    level=record.levelno,
                    pathname=record.pathname,
                    lineno=record.lineno,
                    msg="",
                    args=(),
                    exc_info=None,
                )
            )
        )

    def format(self, record):
        """Format a record with added indentation."""
        indent = " " * self.get_header_length(record)
        head, *trailing = super().format(record).splitlines(True)
        return head + "".join(indent + line for line in trailing)

class Logger:

    def __init__(self,
                 logger_name=None,
                 log_to_file=False,
                 file_dir=None,
                 file_prefix=None,
                 file_append=False,
                 file_loglevel=logging.DEBUG,
                 log_to_console=True,
                 console_loglevel=logging.INFO,
                 print_logger_name=False
                ):
        """Set up logging to file and console."""

        if log_to_file and not file_prefix:
            raise Exception("log_to_file is True, but file_prefix was not provided")

        # Remove old handlers from root logger
        logging.getLogger().handlers.clear()

        # Redirect the warnings.warn() called by pybliometrics
        # when a Scopus ID was merged
        # to the logging system
        logging.captureWarnings(True)

        # Get logger for our module
        self.logger = logging.getLogger(logger_name)
        # Remove old handlers
        self.logger.handlers.clear()
        # Prevents JupyterLab to display output two times
        # See: https://stackoverflow.com/questions/31403679/python-logging-module-duplicated-console-output-ipython-notebook-qtconsole
        self.logger.propagate = False
        # Set root logger's logging level to the lowest possible
        # We will set higher levels in the handlers
        self.logger.setLevel(logging.DEBUG)

        # Log to console
        if log_to_console:
            # make handler that writes to sys.stdout
            console = logging.StreamHandler(stream=sys.stdout)
            console.setLevel(console_loglevel)
            # set a format which is simpler for console use
            fmt = "%(asctime)s "
            if print_logger_name:
                fmt += "%(name)s "
            fmt += "%(levelname)s %(message)s"
            formatter = MultiLineFormatter(
                fmt=fmt,
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            console.setFormatter(formatter)
            # add the handler to the root logger
            self.logger.addHandler(console)

        # Log to file
        if log_to_file:
            if not file_dir:
                file_dir = os.path.join(".", "logs")
            os.makedirs(file_dir, exist_ok=True)
            dt = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            file_name = file_prefix + "_" + dt + ".log"
            if type(file_dir) == str:
                file_dir = pathlib.Path(file_dir)
            file_path = pathlib.Path(file_dir/file_name)
            if file_append:
                file_mode = "a"
            else:
                file_mode = "w"
            file_handler = logging.FileHandler(
                filename=file_path, mode=file_mode, encoding="utf8"
            )
            file_handler.setLevel(file_loglevel)
            # set MultiLineFormatter for file handler
            formatter = MultiLineFormatter(
                fmt="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(formatter)
            # add handler to logger
            self.logger.addHandler(file_handler)

        # Log debug info
        self.logger.info("Started")
        self.logger.info(f"Python executable: {sys.executable}")
        self.logger.info(f"Python version: {sys.version}")

        msg = f"Console handler: {log_to_console}"
        if log_to_console:
            msg += f", level: {logging.getLevelName(console_loglevel)}"
        self.logger.info(msg)

        msg = f"File handler: {log_to_file}"
        if log_to_file:
            msg += f", level {logging.getLevelName(file_loglevel)}, " \
                   f"filename '{file_path.resolve()}', " \
                   f"mode {file_mode}"
        self.logger.info(msg)

    def log_exception(self):
        """
        Call this when we catch an exception
        """
        except_type, except_class, tb = sys.exc_info()
        self.logger.error(f"Exception")
        self.logger.error(f"Type={except_type}")
        self.logger.error(f"Class={except_class}")
        self.logger.error(f"Traceback:")
        for s in traceback.format_tb(tb):
            self.logger.error(s.strip())

    def change_console_loglevel(self, newlevel):
        for handler in self.logger.handlers:
            if isinstance(handler, type(logging.StreamHandler())):
                handler.setLevel(newlevel)

    def change_file_loglevel(self, newlevel):
        for handler in self.logger.handlers:
            if isinstance(handler, type(logging.FileHandler())):
                handler.setLevel(newlevel)

    def debug(self, s):
        self.logger.debug(s)

    def info(self, s):
        self.logger.info(s)

    def warning(self, s):
        self.logger.warning(s)

    def error(self, s):
        self.logger.error(s)


