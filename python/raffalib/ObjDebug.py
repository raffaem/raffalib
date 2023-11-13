#!/usr/bin/env python3
# Copyright 2023 Raffaele Mancuso
# SPDX-License-Identifier: GPL-2.0-or-later

import importlib

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

