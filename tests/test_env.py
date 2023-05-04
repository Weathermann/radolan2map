# test_env.py

import os
import subprocess
import platform
import psutil


def test_print_platform():
    print(platform.platform())
    print("Cores:", os.cpu_count())
    mem = psutil.virtual_memory().total  # total physical memory in Bytes
    print("Mem:", mem)
    
def test_system():
    cmd = "cat /etc/os-release"
    ret = subprocess.call(cmd, shell=True)
    assert ret == 0
