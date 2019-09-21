# -*- coding:utf-8 -*-


import platform
import getpass

from tools import Print,Utils
from atom.common.auth import LinuxSSHAuth
from config import config,GetBaseconfig,DefaultOption
from atom.common import *



cfg = config()
class Check(object):


    def __init__(self):

        pass

        # self.loginUser()
        # self.systemVersion()
        # self.check()

    def systemVersion(self):
        # 检查系统是否为 CentOS7
        linux_distribution = platform.linux_distribution()
        system_version = linux_distribution[1].split('.')[0]

        if 'CentOS' not in linux_distribution[0]:
            Print("The system is {}, must running in CentOS".format(linux_distribution[0]),colour="red")

        if int(system_version) < 7:
            Print("The system is CentOS {}, must running in CentOS 7 or more".format(linux_distribution[1]),colour="red")
        else:
            Print("The system is {} {}".format(linux_distribution[0],linux_distribution[1]),colour="green")

    def check_kernel(self,hostname):
        ip_result = Utils.localCMPHostname(hostname)
        if ip_result:
            res = subprocess.Popen("uname -r",shell=True,stdout=subprocess.PIPE)
            kernel = res.stdout.read().strip()
        else:
            res = run(hostname,"uname -r")
            if res['status']:
                    kernel = res[hostname]['stdout'].strip()
            else:
                kernel = None
                Print("{} Failed to get the kernel version".format(hostname),colour="red")
        kernel_short = float(kernel[0:3])
        if kernel_short < float(4.19):
            Print("Please run: 'python oscar.py -m update -a linux_kernel' to view.",colour="yellow")
            Print("{} kernel version {},Need to upgrade the kernel".format(hostname, kernel), colour="red")
        else:
            Print("{} kernel version {}".format(hostname, kernel),colour="green")


    def loginUser(self):
        user = getpass.getuser()
        if user == 'root':
            Print("The login is root.",colour="green")
        else:
            Print("The login is {},please login for root!".format(user), colour="red")

    def check_vip(self):
        # 检查配置文件中vip和本机ip是否一致
        LB = DefaultOption(cfg,"ha",LB=False).configDict()['LB']
        if not bool(LB):
            VIP = cfg.get("ha","VIP")
            try:
                local_IP = socket.gethostbyname(socket.gethostname())
                if VIP == local_IP:
                    print VIP
                else:
                    Print("VIP should be set to {}".format(local_IP),colour="red")
            except Exception as error:
                print(error)
        else:
            Print("VIP has been set to {}".format(cfg.get("ha","VIP")))

    def check_master(self):
        # 检查给与 k8s 集群 master 是否为本机，且给与的masterIP 不能和 node IP 重复
        MASTER_HOST = GetBaseconfig.MASTER_HOST

        local_hostname = socket.gethostname()

        if local_hostname in MASTER_HOST:

            for masterName in MASTER_HOST:
                ip_result = Utils.localCMPHostname(masterName)
                if ip_result:
                    pass
                else:
                    self.check_ssh(masterName)
        else:
            Print("{} must be in {}".format(local_hostname,MASTER_HOST),colour="yellow")
            Print("{} not Found in {}".format(local_hostname,MASTER_HOST),colour="red")
                # Print("run systemctl stop keepalived",hostname=masterName,colour="yellow")
                # run(hostname=masterName,cmd="systemctl stop keepalived")
        # subprocess.call("systemctl stop keepalived", shell=True)

    def check_node(self):
        NODE = GetBaseconfig.NODE
        for node,nodeName in NODE:
            self.check_ssh(nodeName)

    def check_ssh(self,hostname):
        # 检查给与的 nodes 节点是否能 ssh 连通
        linuxSSHAuth = LinuxSSHAuth(hostname=hostname)
        linuxSSHAuth.auth()
        # linuxSSHAuth = LinuxSSHAuth(hostname=node,username=username,password=password,port=port)

    def check_nfs_client(self,nfs_client,display=True):
        # 检查nfs客户端
        cmd = "kubectl get deployment --all-namespaces ".format(nfs_client)
        p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout = p.stdout.read()
        if nfs_client in stdout:
            if display:
                Print("{} already exists.".format(nfs_client))
        else:
            Print("It can be operated.'python oscar.py -m install -a nfs'",colour="yellow")
            Print("Please install {} first".format(nfs_client),colour="red")

    def check_ingress(self,ingress_name,display=True):
        cmd = "kubectl get pod --all-namespaces ".format(ingress_name)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = p.stdout.read()
        if ingress_name in stdout:
            if display:
                Print("{} already exists.".format(ingress_name))
        else:
            Print("It can be operated.'python oscar.py -m install -a ingress'", colour="yellow")
            Print("Please install {} first".format(ingress_name), colour="red")

    def check_helm(self,helm_server,display=True):
        cmd = "kubectl get deployment --all-namespaces ".format(helm_server)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = p.stdout.read()
        if helm_server in stdout:
            if display:
                Print("{} already exists.".format(helm_server))
                return True
        else:
            from app.install import helmInstall
            helmInstall()
            # Print("It can be operated.'python oscar.py -m install -a helm'", colour="yellow")
            # Print("Please install {} first".format(helm_server), colour="red")