# -*- coding:utf-8 -*-

from paramiko import AutoAddPolicy,AuthenticationException,Transport,SSHClient,ssh_exception
import paramiko
import subprocess
import os
import socket
from utils.config import config,DefaultOption
from tools import Print


cfg = config()

class Common(object):

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    HOSTNAME = socket.gethostname()

    def __init__(self,hostname,port=None,username=None,password=None,pkey=None,timeout=None):

        self.hostname = hostname
        self.port = 22 if port is None else port

        if username is None:
            if "username" not in cfg.options("default"):
                self.username = 'root'
                self.HOME = "/root"
            else:
                self.username = cfg.get("default", "username")
                self.HOME = os.path.join('/home', self.username)
        else:
            if username == 'root':
                self.username = 'root'
                self.HOME = "/root"
            else:
                self.username = username
                self.HOME = os.path.join('/home', self.username)

        if password is None:
            if "password" not in cfg.options("default"):
                self.password = None
            else:
                self.password = cfg.get("default","password")
        else:
            self.password = password

        if pkey is None and password is  None:
            self.pkey = paramiko.RSAKey.from_private_key_file(cfg.get("default","private_key"))
        else:
            self.pkey = None

        self.timeout = 3 if timeout is None else timeout
        self.auth(self.timeout)

    def run(self,cmd,timeout=None):
        # 执行远程shell命令
        if timeout is None:
            timeout = 600
        self.ssh.connect(hostname=self.hostname,port=self.port, username=self.username, password=self.password,
                            pkey=self.pkey, timeout=self.timeout)
        stdin, stdout, stderr = self.ssh.exec_command(cmd,timeout=timeout)
        status = stdout.channel.recv_exit_status()
        return self.format(self.hostname, stdout, stderr, status)


    def sudo(self,cmd,timeout=None):
        # 执行远程sudo命令
        if timeout is None:
            timeout = 600
        self.ssh._transport = self.transport
        # stdin,stdout,stderr = self.ssh.exec_command('sudo sh -c "{}"'.format(cmd),timeout=timeout)
        stdin, stdout, stderr = self.ssh.exec_command('sudo -S sh -c "{}"'.format(cmd), timeout=timeout)
        stdin.write("{}\n".format(self.password))
        stdin.flush()
        status = stdout.channel.recv_exit_status()
        return self.format(self.hostname, stdout, stderr, status)

    def exec_script(self,script,args=None,sudo=False,type=None,display=True):
        # 本地脚本远程执行
        self.initPath()
        destFile_script = os.path.join(self.ATOM_PATH,os.path.split(script)[1])
        self.sftp_upload(script,destFile_script,display=False)

        if args is None:
            if display:
                print("[{}] Executing {} script.".format(self.hostname, script))
            if sudo:
                result = self.sudo("{} {}".format(type,destFile_script))
            else:
                result =self.run("{} {}".format(type,destFile_script))
            return result
        else:
            if display:
                print("[{}] Executing '{} {}' script.".format(self.hostname,script,args))
            if sudo:
                result = self.sudo("{} {} {}".format(type,destFile_script,args))
            else:
                result =self.run("{} {} {}".format(type,destFile_script,args))
            return result

    def sftp_upload(self, source, dest,display=True):
        # 上传文件或者目录
        self.initPath()
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        if os.path.isdir(source):
            if not os.path.isabs(source):
                real_path = os.path.dirname(os.path.realpath(__file__))
                source = os.path.join(real_path, source)

            for root, dirs, files in os.walk(source):

                for filename in files:
                    local_file = os.path.join(root, filename)
                    remote_file = ''.join([dest, local_file.replace(source, '')])
                    try:
                        sftp.put(local_file, remote_file)
                    except Exception as e:
                        sftp.mkdir(os.path.split(remote_file)[0])
                        sftp.put(local_file, remote_file)
                    print("[{}] upload {} to {} success.".format(self.hostname,local_file,remote_file))

                for name in dirs:
                    local_path = os.path.join(root, name)
                    remote_path = ''.join([dest, local_path.replace(source, '')])

                    try:
                        sftp.mkdir(remote_path)
                        print ("[{}] mkdir path {}".format(self.hostname,remote_path))
                    except Exception as error:
                        self.run("mkdir -p {}".format(remote_path))
                        print("[{}] mkdir {} success.".format(self.hostname,remote_path))
        else:
            try:
                sftp.put(source, dest)
                if display is True:
                    print("[{}] upload {} to {} {} success.".format(self.HOSTNAME,source,self.hostname,dest))
            except Exception as error:
                try:
                    sftp.mkdir(os.path.split(dest)[1])
                    if display is True:
                        print ("[{}] mkdir path {}".format(self.hostname, os.path.split(dest)[1]))
                    sftp.put(source, dest)
                    if display is True:
                        print("[{}] upload {} to {} {} success.".format(self.HOSTNAME, source, self.hostname, dest))
                except Exception as error:
                    print ("[{}] {} {}".format(self.HOSTNAME,error,dest))

    def sftp_down_file(self,remotePath,localPath=None):
        # 下载文件
        if localPath is None:
            localPath = os.path.join(os.path.abspath('.'),os.path.split(remotePath)[1])
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        try:
            sftp.get(remotePath,localPath)
        except Exception as e:
            sftp.mkdir(os.path.join(localPath)[1])
            sftp.get(remotePath,localPath)

    def format(self,hostname,stdout,stderr,status):
        if status == 0:
            status = True
        else:
            status = False
        stderr = stderr.read().replace("[sudo] password for {}: ".format(self.username),'')
        result = {hostname: {"stdout":stdout.read(),"stderr":stderr},"status": status}
        return result

    def auth(self,timeout=None):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if timeout is not None:
                sock.settimeout(timeout)
            sock.connect((self.hostname,self.port))
            try:
                self.transport = Transport(self.hostname, self.port)
                if self.password is not None:
                    self.transport.connect(username=self.username, password=self.password)
                else:
                    self.transport.connect(username=self.username,pkey=self.pkey)
            except ssh_exception.SSHException as error:
                raise Exception("{} {}".format(self.hostname, error.message))
        except socket.error as error:
           raise Exception("{} {}".format(self.hostname,error))

    def initPath(self):
        self.ATOM_PATH = os.path.join(self.HOME, '.atom')
        self.run("mkdir {}".format(self.ATOM_PATH))

    def __exit__(self, exc_type, exc_val, exc_tb):

        self.sudo("rm -rf {}".format(self.ATOM_PATH))
        self.ssh.close()
        self.transport.close()

