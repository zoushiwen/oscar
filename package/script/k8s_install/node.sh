#!/usr/bin/env bash

LOG_FILE=$1
master_join=$2
token=$3
ca_hash=$4

function join_node() {

    kubeadm reset -f
    kubeadm join ${master_join} --token ${token} --discovery-token-ca-cert-hash ${ca_hash} >> ${LOG_FILE}

}


join_node

