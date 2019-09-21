#!/usr/bin/env bash


function k8s_remove() {

kubeadm reset -f &>/dev/null
iptables -F && iptables -t nat -F && iptables -t mangle -F && iptables -X
ipvsadm -C &>/dev/null

if [ -d "/var/lib/etcd" ];then
    rm -rf /var/lib/etcd
fi

if [ -d "$HOME/.kube" ];then
    rm -rf $HOME/.kube
fi

}


k8s_remove