#!/usr/bin/env python
# -*- coding:utf-8 -*-

import socket
import sys
import re
import os.path
from config import config,DefaultOption,GetBaseconfig
from atom.common import *

cfg = config()
BASE_DIR = GetBaseconfig.BASE_DIR

class Utils(object):

    def __init__(self):

        pass

    @classmethod
    def getLocalIp(self):
        # 得到本机ip
        localIP = socket.gethostbyname(socket.gethostname())
        return localIP

    @classmethod
    def getHostnameIp(self,hostname):
        # 得到 hostname 的 ip
        try:
            hostnameIP = socket.gethostbyname(hostname)
            return hostnameIP
        except socket.error as error:
            Print("{} {}".format(hostname, error), colour="red")

    @classmethod
    def localCMPHostname(self,hostname):
        # 比较本机ip 和 给与的hostname ip 是否一样
        try:
            localIP = socket.gethostbyname(socket.gethostname())
            hostnameIP = socket.gethostbyname(hostname)
            if localIP == hostnameIP:
                return True
            else:
                return False
        except socket.error as error:
            Print("{} {}".format(hostname,error),colour="red")

    @staticmethod
    def getUserInstallHome():
        # 得到用户的家目录
        username = DefaultOption(cfg,"default",username="root").configDict()
        if username['username'] == 'root':
            k8s_dest_dir = '/root/.atom/package'
        else:
            k8s_dest_dir = "/home/{}/.atom/package".format(username)
        return k8s_dest_dir

def getMasterSSHKey(hostname,username=None,password=None):

    authorized_keys = "/root/.ssh/authorized_keys"
    add_ssh_key_script = os.path.join(BASE_DIR,"package/script/ssh_key/add_ssh_key.sh")

    ## 生成 master 主机的 ssh-key 信息
    id_rsa = "/root/.ssh/id_rsa"
    if not os.path.isfile(id_rsa):
        Print("Keys in production {}".format(id_rsa),colour='green')
        local("ssh-keygen -t rsa  -P '' -f {}".format(id_rsa))

    # 执行脚本，导入ssh key 到其他机器上
    id_rsa_content = readFile("/root/.ssh/id_rsa.pub")
    result = exec_script(hostname=hostname,script=add_ssh_key_script,args="'{}' '{}' '{}'".format(socket.gethostname(),authorized_keys,id_rsa_content),
                         username=username,password=password,sudo=True,display=False)
    if result['status']:
        Print("SSH key add Success.{}".format(result[hostname]['stdout']),colour='green',hostname=hostname)
    else:
        print("[{}] \033[1;31mError: SSH key added Failed. {}\033[0m".format(hostname,result[hostname]['stderr'].strip()))
        Print("Please add the SSH key of {} machine manually".format(hostname),hostname=hostname,colour='yellow')



def readFile(filename):
    # 读文件操作
    with open(filename,'r') as f:
        content = f.read().strip()
    return content

def getJoinInfo(kubeadm_file):

    ## 正则匹配出 join token ca-cert-hash 信息
    # rex = 'kubeadm join (.*?) --token (.*?) --discovery-token-ca-cert-hash (.*)'

    if not os.path.isfile(kubeadm_file):
        raise Exception('{} is not file'.format(kubeadm_file))

    with open(kubeadm_file, 'r') as f:
        content = f.read()
    reg = re.search(r'kubeadm join (.*?) --token (.*?) ', content)
    if reg:
        master_join = reg.group(1)
        token = reg.group(2)
        regx = re.split(r'--discovery-token-ca-cert-hash', content)
        ca_hash = regx[1].strip().split('\n')[0].replace("\\","")
        return master_join,token,ca_hash
    else:
        Print("Not match master_join token ca_hash",colour="red")
        return None,None,None

class Template(object):
    # 模板替换 生成替换后的配置文件
    DEFAULT_UID = 10000
    DEFAULT_GID = 10000

    def mark_file(self,path, mode=0o600, uid=DEFAULT_UID, gid=DEFAULT_GID):
        if mode > 0:
            os.chmod(path, mode)
        if uid > 0 and gid > 0:
            os.chown(path, uid, gid)


    def content(self, src, dest,mode=0o640, uid=0, gid=0,**kwargs):
        file_data = ''
        try:
            with open(src, 'r') as f:
                for line in f:
                    for k,v in kwargs.items():
                        if k in line:
                            format = "${%s}" %k
                            line = line.replace(format, v)
                    file_data += line

            with open(dest, "w") as f:
                f.write(file_data)
            self.mark_file(dest, mode, uid, gid)
            Print("Generated configuration file: {}".format(dest),colour="green")
        except IOError as error:
            print(error)
            sys.exit(1)

def Print(content,hostname=None,colour=None,type=False):

    if hostname is None:
        hostname = socket.gethostname()

    if colour is not None:
        if colour == "red":
            if type:
                print("[{}] \033[1;33mplease view {} error log \033[0m".format(hostname, GetBaseconfig.LOG_FILE))
            print("[{}] \033[1;31mError: {} \nExit installation.\033[0m".format(hostname,content))
            sys.exit(1)
        elif colour == "green":
            print("[{}] \033[1;32m{} \033[0m ".format(hostname,content))
        elif colour == "yellow":
            print("[{}] \033[1;33m{} \033[0m".format(hostname,content))
        else:
            print(content)
    else:
        print(content)
