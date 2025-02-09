__author__ = 'Rachid'

import loadPrint as lp

class Loader(object):
    def __init__(self, precision, multiplier):
        self.precision = precision
        self.multiplier = multiplier

    def __call__(self, fname):
        return lp.load(fname, multiplier=self.multiplier, precision=self.precision)