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
import pathlib
import importlib

import smtplib
import email


def source(file_name, module_name):
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


def send_email(smtp_host,
               smtp_port,
               user,
               password,
               from_email,
               to_email,
               subject,
               message
              ):
    try:
        s = smtplib.SMTP_SSL(host=smtp_host, port=smtp_port)
    except Exception as e:
        logging.error("[send_email] Failed to send e-mail: exception in SMTP_SSL")
        logging.error(e)
        return
    s.ehlo()
    s.login(user, password)

    msg = email.mime.multipart.MIMEMultipart()  # create a message

    # setup the parameters of the message
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # add in the message body
    text = email.mime.text.MIMEText(message, "plain")
    msg.attach(text)
    # msg.attach(MIMEText(message, 'html'))

    # send the message via the server set up earlier.
    try:
        s.send_message(msg)
    except:
        return False
    return True




