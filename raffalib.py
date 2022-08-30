#!/usr/bin/env python3

import logging
import json
import os
import datetime
import sys
import traceback
import pandas as pd
from natsort import natsorted

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def sortcols(df):
    cols = list(df.columns)
    return df[natsorted(cols)]


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


def log_exception():
    except_type, except_class, tb = sys.exc_info()
    logging.error("Exception")
    logging.error(f"Type={except_type}")
    logging.error(f"Class={except_class}")
    logging.error(f"Traceback:")
    for s in traceback.format_tb(tb):
        logging.error(s.strip())


def change_console_loglevel(newlevel):
    logger = logging.getLogger()
    for handler in logger.handlers:
        if isinstance(handler, type(logging.StreamHandler())):
            handler.setLevel(newlevel)


class MultiLineFormatter(logging.Formatter):
    """
    Multi-line formatter.
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


def init_logging(
    module_name,
    log_to_file=True,
    file_dir=None,
    file_prefix=None,
    file_append=False,
    file_loglevel=logging.DEBUG,
    log_to_console=True,
    console_loglevel=logging.INFO,
):

    """Set up logging to file and console."""

    if not file_prefix:
        file_prefix = module_name

    # Remove previous handlers
    logging.getLogger().handlers.clear()

    # Redirect the warnings.warn() called by pybliometrics
    # when a Scopus ID was merged
    # to the logging system
    logging.captureWarnings(True)

    # get logger for our module
    logger = logging.getLogger(module_name)
    # Prevents Jupyter Lab to display output two times
    # see: https://stackoverflow.com/questions/31403679/python-logging-module-duplicated-console-output-ipython-notebook-qtconsole
    logger.propagate = False
    logger.setLevel(logging.DEBUG)

    # Log to console
    if log_to_console:
        # make handler that writes to sys.stdout
        console = logging.StreamHandler(stream=sys.stdout)
        console.setLevel(console_loglevel)
        # set a format which is simpler for console use
        formatter = MultiLineFormatter(
            fmt="%(asctime)s %(levelname)-8s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console.setFormatter(formatter)
        # add the handler to the root logger
        logger.addHandler(console)

    # Log to file
    if log_to_file:
        if not file_dir:
            file_dir = os.path.join(".", "logs")
        os.makedirs(file_dir, exist_ok=True)
        file_name = (
            file_prefix + datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + ".log"
        )
        file_path = os.path.join(file_dir, file_name)
        if file_append:
            file_mode = "a"
        else:
            file_mode = "w"
        file_handler = logging.FileHandler(
            filename=file_path, mode=file_mode, encoding="utf8"
        )
        file_handler.setLevel(file_loglevel)
        # set formatter
        formatter = MultiLineFormatter(
            fmt="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        # add handler to logger
        logger.addHandler(file_handler)

    return logger


def loglevel2str(level):
    if level == 0:
        return "NOTSET"
    elif level == 10:
        return "DEBUG"
    elif level == 20:
        return "INFO"
    elif level == 30:
        return "WARNING"
    elif level == 40:
        return "ERROR"
    elif level == 50:
        return "CRITICAL"
    raise Exception(f"Unrecognized level {level}")


class NumpyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NumpyJSONEncoder, self).default(obj)
