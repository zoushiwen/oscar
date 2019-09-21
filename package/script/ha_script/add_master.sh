#!/usr/bin/env bash



function add_master() {

    mkdir -p ~/ikube/tls

#    sed -i s/MASTER/BACKUP/g /etc/keepalived/keepalived.conf
#    chmod +x /etc/keepalived/check_haproxy.sh
    systemctl restart haproxy
#    systemctl restart keepalived

    echo "------>>>>>>>Cluster add `hostname` master begin.<<<<<<<<<-------"

#    mkdir -p $HOME/.kube
    JOIN_CMD=`kubeadm token create --print-join-command`
    ${JOIN_CMD} --experimental-control-plane
    echo "------>>>>>>>Cluster `hostname` add master finished.<<<<<<-------"

}

add_master
