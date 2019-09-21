# -*- coding:utf-8 -*-

import os
import time
import re
from atom.common import *
from utils.tools import Utils,Print,Template
from utils.config import DefaultOption
from utils.config import config,GetBaseconfig
from utils.check import Check

cfg = config()
template = Template()

LOG_FILE = GetBaseconfig.LOG_FILE
BASE_DIR = GetBaseconfig.BASE_DIR



def helmInstall():
    # 安装 helm
    Print("Staring install helm",colour="green")
    helm_client_package_file = os.path.join(BASE_DIR,"package/helm/helm-v2.14.2-linux-amd64.tar.gz")
    helm_install_script = os.path.join(BASE_DIR,"package/script/helm_install/helm_install.sh")
    helm_install_cmd = "bash {} {}".format(helm_install_script,helm_client_package_file)
    res_status = local(helm_install_cmd)
    if res_status:
        Print("helm install Success.",colour="green")
    else:
        Print("helm install Failed.")

def ingressInstall():
    # 安装 ingress
    Print("Staring install ingress", colour="green")
    time.sleep(3)
    ingress_helm_path = os.path.join(BASE_DIR,"package/helm/nginx-ingress")
    ingress_helm_values = os.path.join(ingress_helm_path,"values.yaml")

    ingress_config = DefaultOption(cfg,"ingress",ingress_name="ingress-nginx",ingress_namespace="kube-system").configDict()

    ingress_cmd = "helm install --name {} -f {} {} --namespace {}".format(ingress_config['ingress_name'],ingress_helm_values,
                                          ingress_helm_path, ingress_config['ingress_namespace'])
    try:
        res_status = local(ingress_cmd)
        if res_status:
            Print("Ingress install Success.",colour="green")
            Print("Please run: 'kubectl get pod -n {}' to view.".format(ingress_config['ingress_namespace']),colour="yellow")
        else:
            print("\033[1;31mError: ingress-nginx already exists or install failed..\033[0m")
    except:
        print("\033[1;31mError: Executing {} Failed,Ingress install Failed.\033[0m".format(ingress_cmd))



def nfsInstall():
    # 安装 nfs-client-provisioner
    Print("Staring install nfs storageClass.", colour="green")
    nfs_helmPath = os.path.join(BASE_DIR,"package/helm/nfs-client-provisioner")
    nfs_helmValues = os.path.join(nfs_helmPath,"values.yaml")
    nfs_install_script = os.path.join(BASE_DIR,"package/script/nfs_install/nfs_install.sh")

    nfs_config= DefaultOption(cfg,"nfs",nfs_name="nfs-client-provisioner",nfs_namespace="kube-system",
                             storageClass_name="nfs-provisioner",nfsServer=GetBaseconfig.NODE_HOST[-1],nfsPath="/nfs/k8s"
                             ).configDict()

    if re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", nfs_config['nfsServer']):
        pass
    else:
        Print("The config.ini nfsServer {} must modify IP Invaild.".format(nfs_config['nfsServer']), colour="red")

    nfsServer = Utils.getHostnameIp(nfs_config['nfsServer'])
    nfs_helm_cmd = "helm install --name {} -f {} {} " \
                   "--set storageClass.name={} " \
                   "--set persistence.nfsServer={} " \
                   "--set persistence.nfsPath={} " \
                   "--namespace {}".format(nfs_config['nfs_name'],nfs_helmValues,nfs_helmPath,nfs_config['storageClass_name'],
                                           nfsServer,nfs_config['nfsPath'],nfs_config['nfs_namespace'])
    print nfs_helm_cmd
    try:
        result = exec_script(hostname=nfs_config['nfsServer'], script=nfs_install_script,
                             args="{}".format(nfs_config['nfsPath']), sudo=True)
        if result['status']:
            Print(result[nfs_config['nfsServer']]['stdout'])
    except Exception as error:
        print(error)

    nfs_status = local(cmd=nfs_helm_cmd)
    if nfs_status:
        Print("nfs-client-provisioner install Success.",colour="green")
        Print("Please run: 'kubectl get pod -n {}' to view.".format(nfs_config['nfs_namespace']),colour="yellow")
    else:
        print("\033[1;31mError: nfs-client-provisioner install Failed.\033[0m")

class Gitlab:

    def __init__(self):

        self.check = Check()
        self.nfs_name = DefaultOption(cfg, "nfs", nfs_name="nfs-client-provisioner").configDict()['nfs_name']
        self.ingress_name = DefaultOption(cfg, "ingress", ingress_name="ingress-nginx").configDict()['ingress_name']

        self.gitlab_yaml_path = os.path.join(BASE_DIR, "package/yaml/gitlab")
        self.gitlab_config = DefaultOption(cfg, "gitlab", gitlab_namespace="gitlab",gitlabRootPassword="gitlab2019",
                                      externalUrl="http://test.gitlab.qihoo.net").configDict()

    def gitlabHelmInstall(self):
        # helm 安装 gitlab
        Print("Staring helm install gitlab", colour="green")
        gitlab_helm_path = os.path.join(BASE_DIR, "package/helm/gitlab-ce")
        gitlab_helm_values = os.path.join(gitlab_helm_path, "values.yaml")
        gitlab_helm_ingress = os.path.join(gitlab_helm_path, "gitlab-ingress.yaml")
        gitlab_helm_ingress_tmp = os.path.join(gitlab_helm_path, "gitlab-ingress.yaml.tmpl")

        # 替换 gitlab-ce 中
        template.content(src=gitlab_helm_ingress_tmp, dest=gitlab_helm_ingress,
                         externalUrl=cfg.get("gitlab", "externalUrl").replace('http://','')
                         )

        gitlab_helm_cmd = "helm install --name {} -f {} {} " \
                          "--set gitlabRootPassword={} " \
                          "--set externalUrl={} " \
                          "--namespace {}".format(self.gitlab_config['gitlab_name'],gitlab_helm_values, gitlab_helm_path,
                                                  self.gitlab_config['gitlabRootPassword'], self.gitlab_config['externalUrl'],self.gitlab_config['gitlab_namespace'])
        print gitlab_helm_cmd
        gitlab_status = local(cmd=gitlab_helm_cmd)

        if gitlab_status:
            Print("Gitlab install Success.",colour="green")
            gitlab_ingress_cmd = "kubectl apply -f {}".format(gitlab_helm_ingress)
            local(cmd=gitlab_ingress_cmd)
            add_url_hosts(self.gitlab_config['externalUrl'].split('//')[1])
            Print("Please run: 'kubectl get pod -n {}' to view.".format(self.gitlab_config['gitlab_namespace']),colour="yellow")
        else:
            print("\033[1;31mError: gitlab install Failed.\033[0m")

    def gitlabYamlInstall(self):
        # yaml 安装 gitlab
        Print("Staring YAML install gitlab", colour="green")
        self.check.check_nfs_client(self.nfs_name,display=False)
        self.check.check_ingress(self.ingress_name,display=False)
        gitlab_yaml_tmp_path = os.path.join(self.gitlab_yaml_path, "tmp")
        gitlab_yaml_gitlab_ce = os.path.join(self.gitlab_yaml_path,"gitlab-ce.yaml")
        gitlab_yaml_gitlab_postgresql = os.path.join(self.gitlab_yaml_path, "gitlab-postgresql.yaml")
        gitlab_yaml_gitlab_redis = os.path.join(self.gitlab_yaml_path, "gitlab-redis.yaml")

        # 替换 gitlab-ce 中
        template.content(src=os.path.join(gitlab_yaml_tmp_path, "gitlab-ce-tmp.yaml"), dest=gitlab_yaml_gitlab_ce,
                         gitlab_namespace=self.gitlab_config['gitlab_namespace'],GITLAB_ROOT_PASSWORD=self.gitlab_config['gitlabRootPassword'],
                         GITLAB_HOST=self.gitlab_config['externalUrl'].split('//')[1],
                         )
        template.content(src=os.path.join(gitlab_yaml_tmp_path, "gitlab-postgresql-tmp.yaml"), dest=gitlab_yaml_gitlab_postgresql,
                         gitlab_namespace=self.gitlab_config['gitlab_namespace']
                         )
        template.content(src=os.path.join(gitlab_yaml_tmp_path, "gitlab-redis-tmp.yaml"),dest=gitlab_yaml_gitlab_redis,
                         gitlab_namespace=self.gitlab_config['gitlab_namespace']
                         )

        gitlab_yaml_cmd = "kubectl apply -f {},{},{}".format(gitlab_yaml_gitlab_ce,gitlab_yaml_gitlab_postgresql,gitlab_yaml_gitlab_redis)

        gitlab_status = local(cmd=gitlab_yaml_cmd)
        if gitlab_status:
            Print("Gitlab YAML install Success.", colour="green")
            GITLAB_HOST = self.gitlab_config['externalUrl'].split('//')[1]
            Print("Import {} to /etc/hosts.".format(GITLAB_HOST), colour="green")
            add_url_hosts(GITLAB_HOST)
            Print("Please run: 'kubectl get pod -n {}' to view.".format(self.gitlab_config['gitlab_namespace']), colour="yellow")
        else:
            print("\033[1;31mError: gitlab install Failed.\033[0m")


    def remove_yaml(self):
        gitlab_yaml_gitlab_ce = os.path.join(self.gitlab_yaml_path, "gitlab-ce.yaml")
        gitlab_yaml_gitlab_postgresql = os.path.join(self.gitlab_yaml_path, "gitlab-postgresql.yaml")
        gitlab_yaml_gitlab_redis = os.path.join(self.gitlab_yaml_path, "gitlab-redis.yaml")

        remove_gitlab_yaml_cmd = "kubectl delete -f {},{},{}".format(gitlab_yaml_gitlab_ce,gitlab_yaml_gitlab_postgresql,gitlab_yaml_gitlab_redis)
        gitlab_status = local(cmd=remove_gitlab_yaml_cmd)
        if gitlab_status:
            Print("Gitlab YAML remove Success.", colour="green")
            Print("Please run: 'kubectl get pod -n {}' to view.".format(self.gitlab_config['gitlab_namespace']), colour="yellow")
        else:
            print("\033[1;31mError: gitlab YAML remove Failed.\033[0m")

class Harbor:

    def __init__(self):

        self.check = Check()
        self.check.check_helm('tiller-deploy',display=False)
        self.harbor_config = DefaultOption(cfg, "harbor", harbor_name="harbor", harbor_namespace="harbor",
                                           storageClass="nfs-provisioner",
                                           harborAdminPassword="Harbor12345").configDict()
    def harborInstall(self):
        # 安装 harbor

        nfs_name = DefaultOption(cfg, "harbor", nfs_name="nfs-client-provisioner").configDict()['nfs_name']
        ingress_name = DefaultOption(cfg, "ingress", ingress_name="ingress-nginx").configDict()['ingress_name']
        self.check.check_nfs_client(nfs_name,display=False)
        self.check.check_ingress(ingress_name,display=False)
        Print("Staring install harbor", colour="green")
        harbor_helm_path = os.path.join(BASE_DIR, "package/helm/harbor-helm")
        harbor_helm_values = os.path.join(harbor_helm_path, "values.yaml")
        harbor_helm_values_tmp = os.path.join(harbor_helm_path, "values_tmp.yaml")


        # 替换 harbor-helm 中 StorageClass
        core_hosts = cfg.get("harbor","externalURL").split('//')[1]
        template.content(src=harbor_helm_values_tmp,dest=harbor_helm_values,
                         storageClass=self.harbor_config['storageClass'],externalURL=cfg.get("harbor","externalURL"),
                         core_hosts=core_hosts,
                         notary_hosts=core_hosts.replace(core_hosts.split('.')[0],'notary')
                         )
        # 导入 docker harbor安装认证url

        harbor_helm_cmd = "helm install --name {} -f {} {} " \
                          "--set harborAdminPassword={} " \
                          "--namespace {}".format(self.harbor_config['harbor_name'],harbor_helm_values, harbor_helm_path,self.harbor_config['harborAdminPassword'],
                                                  self.harbor_config['harbor_namespace'])
        print harbor_helm_cmd
        harbor_status = local(cmd=harbor_helm_cmd)
        if harbor_status:
            Print("harbor install Success.",colour="green")
            self.add_harbor_url_docker(cfg.get("harbor", "externalURL"))
            add_url_hosts(core_hosts)
            Print("Please run: 'kubectl get pod -n {}' to view.".format(self.harbor_config['harbor_namespace']),colour="yellow")
        else:
            print("\033[1;31mError: harbor install Failed.\033[0m")

    def remove_harbor(self):
        remove_harbor_helm_cmd = "helm del --purge {} ".format(self.harbor_config['harbor_name'])
        harbor_status = local(cmd=remove_harbor_helm_cmd)
        if harbor_status:
            Print("helm remove harbor Success.", colour="green")
            remove_harbor_pvc_cmd = "kubectl delete pvc --all -n {}".format(self.harbor_config['harbor_namespace'])
            remove_pvc_status = local(cmd=remove_harbor_pvc_cmd)
            if remove_pvc_status:
                Print("kubectl remove harbor pvc Success.", colour="green")
            else:
                Print("Please run: 'kubectl delete pvc --all -n {}.".format(self.harbor_config['harbor_namespace']),
                      colour="red")
        else:
            print("\033[1;31mError: helm remove harbor Failed.\033[0m")

    def add_harbor_url_docker(self,url):
        Print("import insecure-registries to others node.", colour="green")
        add_harbor_script = os.path.join(GetBaseconfig.BASE_DIR, "package/script/add_hosts/add_harbor_url_docker.py")
        NODE_HOST = GetBaseconfig.NODE_HOST
        MASTER_HOST = GetBaseconfig.MASTER_HOST
        for node in NODE_HOST:
            node_status = exec_script(hostname=node, script=add_harbor_script, args=url, sudo=True, type="python",
                              display=False)
            if node_status['status']:
                Print("{}".format(node_status[node]['stdout'].strip()),hostname=node,colour="green")
                # run(hostname=node, cmd="systemctl daemon-reload && systemctl restart docker")
            else:
                Print("{}".format(node_status[node]['stderr']),hostname=node,colour="yellow")
                Print("Please import manually {} to {} /etc/docker/daemon.json".format(url,node),hostname=node,colour="yellow")

        for master in MASTER_HOST:
            master_status = exec_script(hostname=master, script=add_harbor_script, args=url, sudo=True, type="python",
                              display=False)
            if master_status['status']:
                Print("{}".format(master_status[master]['stdout'].strip()),hostname=master,colour="green")
                # run(hostname=master, cmd="systemctl daemon-reload && systemctl restart docker")
            else:
                Print("{}".format(master_status[master]['stderr']),hostname=master,colour="yellow")
                Print("Please import manually {} to {} /etc/docker/daemon.json".format(url, master), hostname=master,
                      colour="yellow")
        tips = """
                Tips:
                    If you want to docker login {}.
                    Please execute first systemctl daemon-reload && systemctl restart docker.
                """.format(url)
        Print(tips, colour="yellow")

class CephRBD:

    def __init__(self):
        """
            安装 ceph rbd provisioner
        """

        self.ceph_rbd_path = os.path.join(BASE_DIR,"package/yaml/ceph")
        self.ceph_yaml_rbd_deploymemt = os.path.join(self.ceph_rbd_path,"rbd-deployment.yaml")
        self.ceph_yaml_rbd_sa = os.path.join(self.ceph_rbd_path, "rbd-sa.yaml")
        self.cephRBD_config = DefaultOption(cfg, "ceph-rbd", ceph_rbd_namespace="kube-system").configDict()


    def rbdInstall(self):
        Print("Staring YAML install rbd provisioner", colour="green")
        ceph_rbd_tmp_path = os.path.join(self.ceph_rbd_path,"tmp")
        template.content(src=os.path.join(ceph_rbd_tmp_path,"rbd-deployment-tmp.yaml"),dest=self.ceph_yaml_rbd_deploymemt,
                         ceph_rbd_namespace=self.cephRBD_config['ceph_rbd_namespace'])
        template.content(src=os.path.join(ceph_rbd_tmp_path, "rbd-sa-tmp.yaml"), dest=self.ceph_yaml_rbd_sa,
                         ceph_rbd_namespace=self.cephRBD_config['ceph_rbd_namespace'])

        ceph_yaml_rbd_cmd = "kubectl apply -f {},{}".format(self.ceph_yaml_rbd_sa,self.ceph_yaml_rbd_deploymemt)

        ceph_rbd_status = local(cmd=ceph_yaml_rbd_cmd)

        if ceph_rbd_status:
            Print("rbd-provisioner YAML install Success.")
            Print("Please run: 'kubectl get pod -n {}' to view.".format(self.cephRBD_config['ceph_rbd_namespace']),
                  colour="yellow")
        else:
            print("\033[1;31mError: rbd-provisioner YAML install Failed.\033[0m")


    def rbdRemove(self):
        remove_ceph_rbd_cmd = "kubectl delete -f {},{}".format(self.ceph_yaml_rbd_sa,self.ceph_yaml_rbd_deploymemt)

        remove_ceph_rbd_status = local(cmd=remove_ceph_rbd_cmd)
        if remove_ceph_rbd_status:
            Print("rbd-provisioner YAML remove Success.", colour="green")
            Print("Please run: 'kubectl get pod -n {}' to view.".format(self.cephRBD_config['ceph_rbd_namespace']),
                  colour="yellow")
        else:
            print("\033[1;31mError: rbd-provisioner YAML remove Failed.\033[0m")


def add_url_hosts(url):
    # 导入 harbor url 到所以节点上
    Print("import {} to others node /etc/hosts.".format(url), colour="green")
    NODE_HOST = GetBaseconfig.NODE_HOST
    HOST = GetBaseconfig.MASTER_HOST
    HOST.extend(NODE_HOST)
    node_list = list()
    script = os.path.join(GetBaseconfig.BASE_DIR, "package/script/add_hosts/add_hosts.sh")
    for node in NODE_HOST:
        node_IP = Utils.getHostnameIp(node)
        node_list.append(node_IP)
    for i in HOST:
        for j in node_list:
            status = exec_script(hostname=i,script=script, args="{} {}".format(j, url), display=False)
            if status['status']:
                Print("{}".format(status[i]['stdout']))
            else:
                Print("{}".format(status[i]['stderr']))
                Print("Please import manually {} to {}".format(url,i),hostname=i,colour="yellow")


# class InstallK8sCluster(object):
#     """
#         安装k8s集群
#     """
#     base_dir = GetBaseconfig.BASE_DIR
#     package_dir = os.path.join(base_dir, "package")
#     script_dir = os.path.join(package_dir, "script")
#     k8s_install_dir = os.path.join(package_dir,"script/k8s_install")
#     kube_dir = os.path.join(package_dir, "yaml")
#     common_script = os.path.join(k8s_install_dir, "commonInstall.sh")
#     master_script = os.path.join(k8s_install_dir, "master.sh")
#     remove_script = os.path.join(k8s_install_dir,"remove.sh")
#     flannel_yml = os.path.join(kube_dir,"kube","kube-flannel.yml")
#
#     def __init__(self):
#
#
#         self.local_IP = Utils.getLocalIp()
#         self.k8s_dest_dir = Utils.getUserInstallHome()
#         self.node_common_script = os.path.join(self.k8s_dest_dir, "commonInstall.sh")
#         self.node_script = os.path.join(self.k8s_dest_dir,"node.sh")
#         self.node_remove_script = os.path.join(self.k8s_dest_dir,"remove.sh")
#
#     def master(self,hostname):
#         # 安装 master 主节点
#         self.remove(hostname)
#         Print("Start install k8s master {} ...".format(hostname),colour="green")
#         if os.path.isfile(LOG_FILE):
#             os.remove(LOG_FILE)
#
#         common_status = local("bash {} {}".format(self.common_script,LOG_FILE))
#         if common_status:
#             master_status = local("bash {} {} {}".format(self.master_script,LOG_FILE,self.flannel_yml))
#             if master_status:
#                 self.masterJoinInfo()
#                 Print("Info: k8s cluster master {} install success.".format(hostname),colour="green")
#             else:
#                 Print("Error: execute {} error,please check {} log file.".format(self.master_script,LOG_FILE),colour="red")
#         else:
#             Print("Error: execute {} error,please check {} log file".format(self.common_script,LOG_FILE),colour="red")
#
#     def node(self,hostname):
#
#         # 安装 k8s 集群 node 节点
#         self.masterJoinInfo()
#         Print("Start install k8s node {} ...".format(hostname), colour="green")
#         self.remove(hostname)
#         sftp_upload(hostname=hostname, sourceFile=self.k8s_install_dir, destFile=self.k8s_dest_dir)
#         Print("Please view install log file {}:{}".format(hostname,LOG_FILE),hostname=hostname,colour="yellow")
#         Print("Please wait patiently while the program is being installed. It may take several minutes.",hostname=hostname,colour="yellow")
#         node_common_result = sudo(hostname, "/bin/bash {} {}".format(self.node_common_script, LOG_FILE))
#         if node_common_result['status']:
#             node_script_result = sudo(hostname,"/bin/bash {} {} {} {} {}".format(self.node_script,LOG_FILE,self.master_join,self.token,self.ca_hash))
#             if node_script_result['status']:
#                 Print(node_script_result[hostname]['stdout'],hostname=hostname)
#                 Print("node install success",hostname=hostname,colour="green")
#             else:
#                 Print(node_script_result[hostname]['stderr'], hostname=hostname)
#                 Print("node execute {} failed".format(self.node_script),hostname=hostname,colour="yellow")
#         else:
#             Print(node_common_result[hostname]['stderr'],hostname=hostname)
#             Print("node install failed.please check {}:{} log file.".format(hostname,LOG_FILE),hostname=hostname,colour="red")
#
#     def remove(self,hostname):
#         # 安装之前，执行 kubeadm reset
#         ip_result = Utils.localCMPHostname(hostname)
#         if ip_result:
#             local("bash {}".format(self.remove_script))
#         else:
#             run(hostname=hostname,cmd="bash {}".format(self.node_remove_script))
#
#     def masterJoinInfo(self):
#         # 从日志文件中拿到 master token ca_hash
#         self.master_join, self.token, self.ca_hash = getJoinInfo(LOG_FILE)
#         if self.master_join is not None and self.token is not None and self.ca_hash is not None:
#             return self.master_join, self.token, self.ca_hash
#         else:
#             Print("master_join,token,ca_hash not Found.please check {} log file".format(LOG_FILE),colour="red")
#
#     def end(self):
#         # 安装完成之后，打印提示
#         tips ="""
# Tips:
#     Run 'kubectl get nodes' on the control-plane to see this node join the cluster.
#     If the slave node does not join the master node, the following program can be executed.
#     kubeadm join {} --token {} --discovery-token-ca-cert-hash {}
#         """.format(self.master_join, self.token, self.ca_hash)
#         Print(tips,colour="yellow")