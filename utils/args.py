# -*- coding:utf-8 -*-
import argparse
from tools import Print,Utils
from config import GetBaseconfig
from app.install import helmInstall,ingressInstall,nfsInstall
from app.install import Gitlab,Harbor,CephRBD
from app.update import Kernel
from tools import getMasterSSHKey
from app.ha_install import HAk8sCluster
import socket
import time
from check import Check
from atom.common import local


def getArgs():
    CHOINCES = ('k8s','master','node','helm','ingress','nfs','gitlab','harbor','linux_kernel','rbd','test')
    REMOVES = ('gitlab','harbor','rbd')
    parser = argparse.ArgumentParser(description='kubernetes cluster install tools',
                                    epilog="fg: python oscar.py -m install -a k8s")
    parser.add_argument("-m", "--module_name", help="Specified module-name.",choices=('install','update','delete','add_ssh_key'),required=True)
    parser.add_argument("-a", "--args", help="Specified installation type.",choices=CHOINCES,nargs='?')
    parser.add_argument("-d", "--delete", help="Specified remove type.", choices=REMOVES, nargs='?')
    parser.add_argument("-H", "--host", help="please specified update kernel linux machine.")
    parser.add_argument('-u','--username', type=str, help="Enter the login machine username.",nargs='?')
    parser.add_argument('-p','--password', type=str, help="Enter the login machine password.",nargs='?')

    # subparsers = parser.add_subparsers(help="commands")
    # # 增加 add_ssh_key
    # add_ssh_parser = subparsers.add_parser('add_ssh_key',help="Add ssh key to other machines.")
    # add_ssh_parser.add_argument('--username','-u',type=str,help="Enter the login machine username.",required=True)
    # add_ssh_parser.add_argument('--password','-p',type=str,help="Enter the login machine password.",required=True)
    # # 升级内核 update_linux
    # add_ssh_parser = subparsers.add_parser('update_linux', help="Add ssh key to other machines.")
    # add_ssh_parser.add_argument('--hostname', '-H', type=str, help="Enter the login machine hostname.", required=True)

    args = parser.parse_args()
    return args

def oscar():
    args = getArgs()
    check = Check()
    check.loginUser()
    MASTER = GetBaseconfig.MASTER
    NODE = GetBaseconfig.NODE
    masterHostname = [masterHostname for master, masterHostname in MASTER]
    nodeHostname = [nodeHostname for node, nodeHostname in NODE]

    if args.module_name == "install":
        # 安装k8s集群 ha 多master版本
        choices = ('k8s','master','node')
        Print("Start checking the initialization environment ...", colour="green")
        Print("Master: {}.".format(MASTER), colour="green")
        Print("Node: {}.".format(NODE), colour="green")

        if args.args == "k8s":

            # 检查 master node 机器是否能连通
            check.check_vip()
            check.check_master()
            check.check_node()

            # 检查 机器内核版本
            for masterName in masterHostname:
                check.check_kernel(masterName)

            for masterName in masterHostname:
                HAk8sCluster(masterName).install_master()
            for nodeName in nodeHostname:
                HAk8sCluster(nodeName).install_node()
            # helmInstall()
            HAk8sCluster.end()

        elif args.args == "master":
            check.check_master()
            for masterName in masterHostname:
                HAk8sCluster(masterName,).install_master()
        elif args.args == "node":
            check.check_node()
            for nodeName in nodeHostname:
                HAk8sCluster(nodeName).install_node()
            HAk8sCluster.end()

        elif args.args == "helm":
            helmInstall()

        elif args.args == "ingress":

            status = check.check_helm('tiller-deploy')
            if status:
                ingressInstall()
            else:
                for i in range(1,10):
                    time.sleep(10)
                    status = check.check_helm('tiller-deploy')
                    if status:
                        ingressInstall()
                        break
                    else:
                        Print("\033[1;31mWarning: Ingress try it for {}...\033[0m".format(i),colour="yellow")
                        if i == 9:
                            Print("Please try again later to ensure that the helm installation is successful",
                                  colour="yellow")
                            print("\033[1;31mError: Ingress install Failed.\033[0m")
                        else:
                            continue

        elif args.args == "nfs":
            check.check_helm('tiller-deploy')
            nfsInstall()
        elif args.args == "gitlab":
            Gitlab().gitlabYamlInstall()
        elif args.args == "harbor":
            Harbor().harborInstall()
        elif args.args == "rbd":
            CephRBD().rbdInstall()
        elif args.args == "test":
            from atom.common import run
            print run(hostname='localhost',cmd='ls /home')
        else:
            print ("Error: Not Found {}.Please enter the parameters correctly".format(args.args))

    elif args.module_name == "delete":

        if args.delete == "gitlab":
            Gitlab().remove_yaml()
        elif args.delete == "harbor":
            Harbor().remove_harbor()
        elif args.delete == "rbd":
            CephRBD().rbdRemove()
        else:
            print ("Error: Not Found args.Please enter the parameters correctly.")


    elif args.module_name == "update":

        kernel = Kernel()
        check.check_master()

        # 升级 master 节点内核版本
        if args.args == "linux_kernel":
            check.check_master()
            update_kernel_status = raw_input("[execute [update linux kernel] ?( yes/no)] ")
            if update_kernel_status == "yes":
                kernel.other_kernel()
                kernel.local_kernel()
            else:
                Print("Exit the update kernel.",colour="red")
        else:
            print ("Error: Not Found args.Please enter the parameters correctly.")

         # 指定Linux升级内核版本
        if args.host:
            kernel.update_linux_kernel(args.host)

    elif args.module_name == "add_ssh_key":
        try:
            username = args.username
            password = args.password
            masterName = [ masterName for masterName in masterHostname if masterName != socket.gethostname()]
            nodeHostname.extend(masterName)
            for hostname in nodeHostname:
                getMasterSSHKey(hostname=hostname,username=username,password=password)
        except:
            Print('Getting username or password parameter error.',colour="yellow")
