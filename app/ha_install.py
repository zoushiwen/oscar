# -*- coding:utf-8 -*-

from utils.tools import Utils,Print,Template,getJoinInfo
import os,sys,stat
import shutil
from atom.common import *
from utils.tools import cfg
from utils.config import GetBaseconfig,DefaultOption

base_dir = GetBaseconfig.BASE_DIR
LOG_FILE = GetBaseconfig.LOG_FILE
K8S_DEST_DIR = Utils.getUserInstallHome()
kernel_dir = os.path.join(base_dir, "package/kernel")
ha_config = os.path.join(base_dir,"package/ha_config")
ha_script = os.path.join(base_dir,"package/script/ha_script")

kube_flannel_yml = os.path.join(base_dir,"package/yaml/kube","kube-flannel.yml")



class HAk8sCluster(object):
    VIP = cfg.get("ha", "VIP")
    base_dir = GetBaseconfig.BASE_DIR
    package_dir = os.path.join(base_dir, "package")
    script_dir = os.path.join(package_dir, "script")
    k8s_install_dir = os.path.join(package_dir, "script/k8s_install")
    MASTER0_IP = Utils.getHostnameIp(cfg.get("master", "MASTER0"))
    MASTER1_IP = Utils.getHostnameIp(cfg.get("master", "MASTER1"))
    MASTER2_IP = Utils.getHostnameIp(cfg.get("master", "MASTER2"))



    def __init__(self,hostname):
        self.hostname = hostname
        self.ip_result = Utils.localCMPHostname(hostname)  # 判断是否为本机上执行安装 True 为是，False 不是；
        self.template = Template()
        self.k8s_dest_dir = Utils.getUserInstallHome()
        self.node_common_script = os.path.join(ha_script, "commonInstall.sh")
        self.node_script = os.path.join(ha_script, "node.sh")
        self.ha_k8s_config = DefaultOption(cfg,"ha",LB=False,CIDR="10.244.0.0/16").configDict()
        # self.generateHAconfig()

    def install_master(self):
        # 安装 ha install
        Print("Staring ha install Master {}".format(self.hostname),hostname=self.hostname,colour="green")
        Print("Please view install log file {}:{}".format(self.hostname,LOG_FILE),hostname=self.hostname,colour="yellow")
        commonHAMaster_script = os.path.join(ha_script, "commonHAMaster.sh")
        ha_master_script = os.path.join(ha_script,"ha_master.sh")
        add_master_script = os.path.join(ha_script, "add_master.sh")

        # kubeadm reset -f
        self.remove()

        if self.ip_result:
            result_status = local("bash {} {}".format(commonHAMaster_script,LOG_FILE))
            Print("Please wait patiently while the program is being installed. It may take several minutes.",
                  hostname=self.hostname, colour="yellow")
            if result_status:
                self.generateHAconfig()
                status =  local("bash {} {} {}".format(ha_master_script,kube_flannel_yml,LOG_FILE))
                if status:
                    Print("Install Master success",hostname=self.hostname,colour="green")
                else:
                    Print("Install Master Failed",hostname=self.hostname, colour="red",type=True)
            else:

                Print("{} install script Failed.".format(commonHAMaster_script),colour="red",type=True)
        else:
            Print("Please wait patiently while the program is being installed. It may take several minutes.",
                  hostname=self.hostname, colour="yellow")
            result_script = exec_script(self.hostname,script=commonHAMaster_script,args="{}".format(LOG_FILE),sudo=True)
            result_status = result_script['status']
            if result_status:
                self.upload_HA_master_file()
                result_add_master_script = exec_script(hostname=self.hostname,script="{}".format(add_master_script))
                try:
                    if result_add_master_script['status']:
                        Print(result_add_master_script[self.hostname]['stdout'], hostname=self.hostname)
                        Print("{} add master success.".format(self.hostname,add_master_script),colour="green")
                except Exception as error:
                    raise Exception("{} failed".format(add_master_script))
            else:
                Print("{} exec failed".format(commonHAMaster_script),hostname=self.hostname,colour="yellow")


    def install_node(self):

        # 安装 k8s 集群 node 节点
        self.masterJoinInfo()
        Print("Start install k8s node {} ...".format(self.hostname), colour="green")
        self.remove()
        Print("Please view install log file {}:{}".format(self.hostname,LOG_FILE),hostname=self.hostname,colour="yellow")
        Print("Please wait patiently while the program is being installed. It may take several minutes.",hostname=self.hostname,colour="yellow")
        node_common_result = exec_script(hostname=self.hostname, script=self.node_common_script,args="{}".format(LOG_FILE))
        if node_common_result['status']:
            node_script_result = exec_script(hostname=self.hostname,script=self.node_script,args="{} {} {} {}".format(LOG_FILE,self.master_join,self.token,self.ca_hash))
            if node_script_result['status']:
                Print(node_script_result[self.hostname]['stdout'],hostname=self.hostname)
                Print("node install success",hostname=self.hostname,colour="green")
            else:
                Print(node_script_result[self.hostname]['stderr'], hostname=self.hostname)
                Print("node execute {} failed".format(self.node_script),hostname=self.hostname,colour="yellow")
        else:
            Print(node_common_result[self.hostname]['stderr'],hostname=self.hostname)
            Print("node install failed.please check {}:{} log file.".format(self.hostname,LOG_FILE),hostname=self.hostname,colour="red",type=True)

    def generateHAconfig(self):
        # 生成ha的配置文件
        # generate cluster_info
        self.template.content(os.path.join(ha_config,"cluster-info"),"/cluster-info",
                        CP0_IP=self.MASTER0_IP,CP0_HOSTNAME=cfg.get("master","MASTER0"),
                        CP1_IP=self.MASTER1_IP,CP1_HOSTNAME=cfg.get("master","MASTER1"),
                        CP2_IP=self.MASTER2_IP,CP2_HOSTNAME=cfg.get("master","MASTER2"),
                        VIP=self.VIP
                         )

        # generate haproxy.cfg
        self.template.content(os.path.join(ha_config,"haproxy.cfg"),"/etc/haproxy/haproxy.cfg",
                        MASTER0_IP=self.MASTER0_IP,CP0_HOSTNAME=cfg.get("master","MASTER0"),
                        MASTER1_IP=self.MASTER1_IP,CP1_HOSTNAME=cfg.get("master","MASTER1"),
                        MASTER2_IP=self.MASTER2_IP,CP2_HOSTNAME=cfg.get("master","MASTER2"),
                         )
        # generate /etc/keepalived/keepalived.conf
        # self.template.content(os.path.join(ha_config,"keepalived.conf"),"/etc/keepalived/keepalived.conf",
        #                  CP0_IP=self.MASTER0_IP,
        #                  CP1_IP=self.MASTER1_IP,
        #                  CP2_IP=self.MASTER2_IP,
        #                  VIP=self.VIP,
        #                  PRIORITY=self.num
        #                  )
        # generate /etc/kubernetes/kubeadm-config.yaml
        self.template.content(os.path.join(ha_config,"kubeadm-config.yaml"),"/etc/kubernetes/kubeadm-config.yaml",
                        CP0_IP=self.MASTER0_IP,
                        CP1_IP=self.MASTER1_IP,
                        CP2_IP=self.MASTER2_IP,
                        VIP=self.VIP,
                        CIDR = self.ha_k8s_config['CIDR']
                         )

        # shutil.copy(os.path.join(ha_config,"check_haproxy.sh"),"/etc/keepalived/check_haproxy.sh")
        # os.chmod('/etc/keepalived/check_haproxy.sh', stat.S_IXGRP)

    def upload_HA_master_file(self):
        # 上传 证书到其他 master 上
        # self.template.content(os.path.join(ha_config, "keepalived.conf"), "/tmp/keepalived.conf.tmp",
        #                  CP0_IP=self.MASTER0_IP,
        #                  CP1_IP=self.MASTER1_IP,
        #                  CP2_IP=self.MASTER2_IP,
        #                  VIP=self.VIP,
        #                  PRIORITY=self.num
        #                  )
        pki_ca_crt = '/etc/kubernetes/pki/ca.crt'
        pki_ca_key = '/etc/kubernetes/pki/ca.key'
        pki_sa_key = '/etc/kubernetes/pki/sa.key'
        pki_sa_pub = '/etc/kubernetes/pki/sa.pub'
        front_proxy_ca ='/etc/kubernetes/pki/front-proxy-ca.crt'
        front_proxy_key ='/etc/kubernetes/pki/front-proxy-ca.key'
        etcd_ca_crt ='/etc/kubernetes/pki/etcd/ca.crt'
        etcd_ca_key ='/etc/kubernetes/pki/etcd/ca.key'
        admin_config = '/etc/kubernetes/admin.conf'
        cluster_info = '/cluster-info'
        haproxy_config = '/etc/haproxy/haproxy.cfg'
        # check_haproxy = '/etc/keepalived/check_haproxy.sh'
        # keepalived_config = '/etc/keepalived/keepalived.conf'
        # kubeadm_config = '/etc/kubernetes/kubeadm-config.yaml'
        listFile = (pki_ca_crt,pki_ca_key,pki_sa_key,pki_sa_pub,front_proxy_ca,front_proxy_key,etcd_ca_crt,etcd_ca_key,
                    admin_config,cluster_info,haproxy_config)
        for file in listFile:
            sftp_upload(self.hostname,file,file)
        sftp_upload(self.hostname,"/etc/kubernetes/admin.conf","/root/.kube/config")
        # sftp_upload(self.hostname,"/tmp/keepalived.conf.tmp","/etc/keepalived/keepalived.conf")
        #
        # if os.path.isfile("/tmp/keepalived.conf.tmp"):
        #     os.remove("/tmp/keepalived.conf.tmp")

    def masterJoinInfo(self):
        # 从日志文件中拿到 master token ca_hash
        self.master_join, self.token, self.ca_hash = getJoinInfo(LOG_FILE)
        if self.master_join is not None and self.token is not None and self.ca_hash is not None:
            return self.master_join, self.token, self.ca_hash
        else:
            Print("master_join,token,ca_hash not Found.please check {} log file".format(LOG_FILE),colour="red",type=True)


    def remove(self):
        # 安装之前，执行 kubeadm reset
        remove_script = os.path.join(ha_script, "remove.sh")
        if self.ip_result:
            if os.path.isfile(LOG_FILE):
                os.system("rm -f {}".format(LOG_FILE))
            local("bash {}".format(remove_script))
        else:
            exec_script(hostname=self.hostname,script=remove_script)

    @staticmethod
    def end():
            # 安装完成之后，打印提示
            master_join, token,ca_hash = getJoinInfo(LOG_FILE)
            tips = """
    Tips:
        Run 'kubectl get nodes' on the control-plane to see this node join the cluster.
        If the slave node does not join the master node, the following program can be executed.
        kubeadm join {} --token {} --discovery-token-ca-cert-hash {}
        
        k8s 集群已经在主节点上调度pod，如果你不需要在主节点上调度pod请执行以下命令
        "kubectl taint nodes --all node-role.kubernetes.io/master="
        
            """.format(master_join, token, ca_hash)
            local("kubectl taint nodes --all node-role.kubernetes.io/master-")
            Print(tips, colour="yellow")


