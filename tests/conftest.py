# Makes `ltltwin` importable and tests runnable from any working directory (pytest rootdir = repo root).
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # repo root
