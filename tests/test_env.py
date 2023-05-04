# test_env.py

import subprocess


def test_system():
    cmd = "cat /etc/os-release"
    ret = subprocess.call(cmd, shell=True)
    assert ret == 0
