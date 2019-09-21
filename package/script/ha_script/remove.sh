#!/usr/bin/env bash


function remove() {
    if [ -d "$@" ];then
        rm -rf $@
    elif [ -f "$@" ];then
        rm -rf $@
    fi
}


function k8s_remove() {

echo -e "starting kubeadm reset."
kubeadm reset -f >/dev/null 2>&1
iptables -F && iptables -t nat -F && iptables -t mangle -F && iptables -X
ipvsadm -C &>/dev/null

remove "/root/.k8s.log"
remove "/var/lib/etcd"
remove "/etc/kubernetes/pki/"
remove "$HOME/.kube"
mkdir $HOME/.kube
}



k8s_remove