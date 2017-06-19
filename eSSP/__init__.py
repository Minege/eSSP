import os
from ctypes import cdll
from .eSSP import eSSP

eSSP.essp = cdll.LoadLibrary(os.path.join(os.path.dirname(__file__), "libessp.so"))
