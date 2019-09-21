# -*- coding:utf-8 -*-

import socket
from utils.tools import Utils,Print
from paramiko import Transport,SSHException,ssh_exception ,SSHClient,AutoAddPolicy
import paramiko
class LinuxSSHAuth:
    """
        Verify that Linux machines are SSH connected
    """
    def __init__(self,hostname,port=None,username=None,password=None,private_key=None,timeout=None):

        self.hostname = hostname
        self.username = 'root' if username is None else username
        self.port = 22 if port is None else port
        self.timeout = 3 if timeout is None else timeout

        self.password = password

        if private_key is not None:
            self.private = private_key
        else:
            self.private = '/root/.ssh/id_rsa'

    def auth(self):

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.hostname,self.port))
            self.ssh_check(sock=sock)
        except socket.error as error:
            Print ("{} {} {}".format(self.hostname,self.username,error),colour="red")

    def ssh_check(self,sock):
        private_key = paramiko.RSAKey.from_private_key_file(self.private)
        transport= Transport(sock=sock)
        try:
            transport.start_client()
        except SSHException as error:
            Print("{} {}".format(self.username,error),colour="red")
        try:
            if self.password is None:
                transport.auth_publickey(self.username,private_key)
            else:
                transport.auth_password(self.username, self.password)
            if transport.is_authenticated():
                Print("{} {} connection Successfully.".format(self.hostname,self.username),colour="green")
        except ssh_exception.SSHException, e:
            print("{} {}".format(self.hostname,e.message))
            Print ("{} {} Error in username or password.".format(self.hostname,self.username),colour="red")


