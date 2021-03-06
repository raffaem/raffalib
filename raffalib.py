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

def send_email(smtp_host, smtp_port, user, password, from_email, to_email, subject, message):
    try:
        s = smtplib.SMTP_SSL(host=smtp_host, port=smtp_port)
    except Exception as e:
        logging.error("[send_email] Failed to send e-mail: exception in SMTP_SSL")
        logging.error(e)
        return
    s.ehlo()
    s.login(user, password)

    msg = MIMEMultipart()       # create a message

    # setup the parameters of the message
    msg['From']=from_email
    msg['To']=to_email
    msg['Subject']=subject

    # add in the message body
    msg.attach(MIMEText(message, 'plain'))
    #msg.attach(MIMEText(message, 'html'))

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


def init_logging(module_name,
                log_to_file=True, 
                file_path=None,
                file_prefix=None, 
                file_append=False,
                file_loglevel=logging.DEBUG,
                log_to_console=True,
                console_loglevel=logging.INFO):

    """Set up logging to file and console."""

    if not file_prefix:
        file_prefix = module_name

    # Remove previous handlers
    logging.getLogger().handlers.clear()

    # Set DEBUG level on root logger
    # This is essential to have Jupyter Lab
    # print INFO-level messages to the console
    # we will set the log level on a 
    # per-handler basis afterwards
    #logging.getLogger().setLevel(logging.DEBUG)

    # Redirect the warnings.warn() called by pybliometrics
    # when a Scopus ID was merged
    # to the logging system
    logging.captureWarnings(True)

    # get logger for our module
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    # Log to console
    if log_to_console:
        # define a Handler which writes INFO messages or higher to the sys.stderr
        console = logging.StreamHandler(stream=sys.stdout)
        console.setLevel(console_loglevel)
        # set a format which is simpler for console use
        formatter = logging.Formatter("%(asctime)s %(message)s")
        console.setFormatter(formatter)
        # add the handler to the root logger
        logger.addHandler(console)

    # Log to file
    if log_to_file:
        if not file_path:
            os.makedirs(os.path.join(".", "logs"), exist_ok=True)
            filename = file_prefix + datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")+".log"
            file_path = os.path.join(".", "logs", filename)
        if file_append:
            filemode = 'a'
        else:
            filemode = 'w'
        file = logging.FileHandler(filename=file_path, mode=filemode, encoding="utf8")
        file.setLevel(file_loglevel)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s")
        file.setFormatter(formatter)
        logger.addHandler(file)
        
    return logger

def loglevel2str(level):
    if level==0:
        return "NOTSET"
    elif level==10:
        return "DEBUG"
    elif level==20:
        return "INFO"
    elif level==30:
        return "WARNING"
    elif level==40:
        return "ERROR"
    elif level==50:
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
