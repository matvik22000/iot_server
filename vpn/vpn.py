import pexpect


def create_client(name):
    p = pexpect.spawn('/bin/bash -c "../wireguard-install.sh"', timeout=1)
    try:
        p.expect("Select an option")
        p.sendline('1')
        p.expect("exceed 15 chars.")
        p.sendline(name)
        p.sendline("\n")
        p.sendline("\n")
        p.expect("It is also available in ")
        res = p.before.decode()
        p.terminate()
        return res
    except pexpect.exceptions.TIMEOUT:
        p.terminate()
        return None
