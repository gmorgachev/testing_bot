import sys
import json
import argparse

from time import sleep
from lib.runner import RemoteWorker

parser = argparse.ArgumentParser(description='Path to file.')
parser.add_argument('cfg_path', metavar='cfg_path', type=str)
parser.add_argument('params_path', metavar='params_path', type=str)
args = parser.parse_args()

print("worker")
RemoteWorker.remote_run(args.cfg_path, args.params_path)
