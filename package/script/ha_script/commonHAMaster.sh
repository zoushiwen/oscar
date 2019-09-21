#!/usr/bin/env bash

green='\e[1;32m' # green
red='\e[1;31m' # red
nc='\e[0m' # normal


LOG_FILE=$1

function init() {

    swapoff -a && sysctl -w vm.swappiness=0
    sed  -i '/\s\+swap\s\+/d' /etc/fstab
    setenforce 0
    systemctl mask iptables
    systemctl mask ip6tables
    systemctl mask firewalld
    systemctl disable firewalld
    systemctl stop firewalld
    sysctl net.bridge.bridge-nf-call-iptables=1
    # 创建加速器文件
    echo -e "创建 /etc/docker /etc/docker/daemon.json"
    mkdir -p /etc/docker && touch /etc/docker/daemon.json
    mkdir -p /etc/kubernetes/pki/etcd
cat > /etc/docker/daemon.json <<EOF
{
  	"registry-mirrors": ["https://registry.docker-cn.com"]
}
EOF

}

function install(){
	echo -n "Install $@ ..."
	sleep 0.3
	yum  install -y $@ >> $LOG_FILE
	i=$?
	sleep 0.3
	if [ $i == 0 ];then
		echo -e "[${green}$@ Install Success${nc}]"
	else
		echo -e "[${red}$@ Install Failed${nc}]"
		echo "Please check your log file ${LOG_FILE}.."
		exit 3
	fi
}

function remove(){
	echo -n "Remove $@ ..."
	STRING=$(rpm -qa |grep $@)
	if [ -n "${STRING}" ];then
	    yum  remove -y $@ >> $LOG_FILE
	fi
	i=$?
	if [ $i == 0 ];then
		echo -e "[${green}$@ Remove Success${nc}]"
	else
		echo -e "[${red}$@ Remove Failed${nc}]"
	fi
}

function install_cluster() {
# 移除老版本 Docker
echo -e "删除老版本 docker docker-common docker-selinux docker-engine..."
remove docker
remove docker-common
remove docker-selinux
remove docker-engine
wget -O /etc/yum.repos.d/CentOS.repo http://mirrors.aliyun.com/repo/Centos-7.repo >/dev/null 2>&1
# 设置阿里云镜像站加速
curl -s http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo > /etc/yum.repos.d/docker-ce.repo

# 更新 repo
yum makecache fast >> $LOG_FILE
# 安装 ha
install socat ipvsadm ipset haproxy

systemctl enable haproxy
# 安装新版 Docker 依赖
install nfs-utils #安装nfs client
install socat
install yum-utils
install device-mapper-persistent-data
install lvm2
# 安装 Docker
install docker-ce-18.09.8-3.el7 docker-ce-cli-18.09.8-3.el7
# 设置开机启动并运行 Docker
systemctl enable docker >> $LOG_FILE
systemctl daemon-reload >> $LOG_FILE
systemctl restart docker >> $LOG_FILE

}

function install_kubeadm() {
# 添加阿里云镜像软件源
cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg https://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg
EOF

install kubelet-1.15.0
install kubectl-1.15.0
# 安装 kubeadm
install kubeadm-1.15.0
# 设置 kubelet 开机启动并立即启动
systemctl disable kubelet >> $LOG_FILE
systemctl enable kubelet >> $LOG_FILE
systemctl start kubelet >> $LOG_FILE

}

function config_lvs() {

cat > /etc/sysconfig/modules/ipvs.modules <<EOF

#!/bin/bash
ipvs_modules="ip_vs ip_vs_lc ip_vs_wlc ip_vs_rr ip_vs_wrr ip_vs_lblc ip_vs_lblcr ip_vs_dh ip_vs_sh ip_vs_fo ip_vs_nq ip_vs_sed ip_vs_ftp nf_conntrack_ipv4"
for kernel_module in \${ipvs_modules}; do
 /sbin/modinfo -F filename \${kernel_module} > /dev/null 2>&1
 if [ $? -eq 0 ]; then
 /sbin/modprobe \${kernel_module}
 fi
done
EOF
chmod 755 /etc/sysconfig/modules/ipvs.modules && bash /etc/sysconfig/modules/ipvs.modules && lsmod | grep ip_vs >/dev/null 2>&1
}



function pull_images() {

images=($(kubeadm config images list 2>/dev/null | awk -F'/' '{print $2}')) >/dev/null 2>&1
for imageName in ${images[@]} ; do

#    echo "docker pull registry.cn-hangzhou.aliyuncs.com/image-mirror/${imageName}"
    docker pull registry.cn-hangzhou.aliyuncs.com/image-mirror/${imageName} >> $LOG_FILE
#    echo "docker tag registry.cn-hangzhou.aliyuncs.com/image-mirror/${imageName} k8s.gcr.io/${imageName}"
    docker tag registry.cn-hangzhou.aliyuncs.com/image-mirror/${imageName} k8s.gcr.io/${imageName} >> $LOG_FILE
#    echo "docker tag registry.cn-hangzhou.aliyuncs.com/image-mirror/${imageName} k8s.gcr.io/${imageName}"
    docker rmi registry.cn-hangzhou.aliyuncs.com/image-mirror/${imageName} >> $LOG_FILE
    echo -e "[${green}pull k8s images ${imageName} success${nc}]"
done

docker pull registry.cn-hangzhou.aliyuncs.com/image-mirror/flannel:v0.11.0-amd64 >> $LOG_FILE
docker tag  registry.cn-hangzhou.aliyuncs.com/image-mirror/flannel:v0.11.0-amd64  quay.io/coreos/flannel:v0.11.0-amd64 >> $LOG_FILE
docker rmi  registry.cn-hangzhou.aliyuncs.com/image-mirror/flannel:v0.11.0-amd64 >> $LOG_FILE
echo -e "[${green}pull k8s images quay.io/coreos/flannel:v0.11.0-amd64 success${nc}]"

}


init
install_cluster
install_kubeadm
#config_lvs
pull_images