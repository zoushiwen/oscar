#!/usr/bin/env bash

#LOG_FILE=$1
kube_flannel=$1
#
#
LOG_FILE=$2

green='\e[1;32m' # green
red='\e[1;31m' # red
nc='\e[0m' # normal

function master() {


systemctl restart haproxy
## --kubernetes-version=v1.15.0 指定版本
version=$(kubeadm config images list | head -1 | awk -F: '{ print $2 }') &>/dev/null
sed -i s/VERSION/${version}/g /etc/kubernetes/kubeadm-config.yaml

# 在执行以下命令之前需要在上个步骤设置 kubeadm init 加上参数 --pod-network-cidr=10.244.0.0/16
kubeadm init --config /etc/kubernetes/kubeadm-config.yaml >> $LOG_FILE

i=$?
sleep 0.3
if [ $i == 0 ];then
    echo -e "[${green}kubeadm init Success${nc}]"
else
    echo -e "[${red}kubeadm init Failed${nc}]"
    echo "Please check your log file ${LOG_FILE}.."
    exit 3
fi

mkdir -p $HOME/.kube
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config

## 如果你使用 calico 或者flannel网络,必须加上参数 --pod-network-cidr=10.244.0.0/16 用于指定 CNI 部署的网段
kubectl  apply --kubeconfig  /etc/kubernetes/admin.conf -f ${kube_flannel}
}






master
###add_master