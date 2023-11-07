#!/usr/bin/env python3
# Copyright 2023 Raffaele Mancuso
# SPDX-License-Identifier: GPL-2.0-or-later

import logging
import json
import os
import datetime
import sys
import traceback
import pandas as pd
from natsort import natsorted
from pathlib import Path
import importlib

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class ObjDebug(object):
    """
    Class to automatically reload module when it changes.
    See: https://stackoverflow.com/a/77307755/1719931
    """
    def __getattribute__(self,k):
        ga=object.__getattribute__
        sa=object.__setattr__
        cls=ga(self,'__class__')
        modname=cls.__module__
        mod=__import__(modname)
        importlib.reload(mod)
        sa(self,'__class__',getattr(mod,cls.__name__))
        return ga(self,k)


def load_module(file_name, module_name):
    """
    Function to source a Python file
    See: https://stackoverflow.com/a/67208147/1719931
    See: https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    """
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location(module_name, file_name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def ini_db_litestream(con):
    cur = con.cursor()
    cur.execute("PRAGMA busy_timeout = 5000;")
    # cur.execute("PRAGMA journal_mode=WAL;")
    # commit before turning synchronous to normal
    # otherwise sqlite3 fails with
    # OperationalError: Safety level may not be changed inside a transaction
    # con.commit()
    # cur.execute("PRAGMA synchronous = NORMAL;")
    # cur.execute("PRAGMA wal_autocheckpoint = 0;")
    con.commit()


def send_email(
    smtp_host, smtp_port, user, password, from_email, to_email, subject, message
):
    try:
        s = smtplib.SMTP_SSL(host=smtp_host, port=smtp_port)
    except Exception as e:
        logging.error("[send_email] Failed to send e-mail: exception in SMTP_SSL")
        logging.error(e)
        return
    s.ehlo()
    s.login(user, password)

    msg = MIMEMultipart()  # create a message

    # setup the parameters of the message
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # add in the message body
    msg.attach(MIMEText(message, "plain"))
    # msg.attach(MIMEText(message, 'html'))

    # send the message via the server set up earlier.
    try:
        s.send_message(msg)
    except:
        return False
    return True


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


class MyLogger:

    def __init__(self,
                 logger_name=None,
                 log_to_file=True,
                 file_dir=None,
                 file_prefix=None,
                 file_append=False,
                 file_loglevel=logging.DEBUG,
                 log_to_console=True,
                 console_loglevel=logging.INFO,
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
            formatter = MultiLineFormatter(
                fmt="%(asctime)s %(levelname)s %(message)s",
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
                file_dir = Path(file_dir)
            file_path = Path(file_dir/file_name)
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
        if log_to_console:
            self.logger.info(f"Console handler: {log_to_console}, " \
                        f"level {logging.getLevelName(console_loglevel)}")
        if log_to_file:
            self.logger.info(f"File handler: {log_to_file}, " \
                        f"level {logging.getLevelName(file_loglevel)}, " \
                        f"filename '{file_path.resolve()}', " \
                        f"mode {file_mode}")

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
