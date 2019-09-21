#!/usr/bin/env bash

host_IP=$1
URL=$2

function init_add_hosts() {
# 导入host /etc/hosts
CONTENT=$(cat /etc/hosts |grep "${host_IP} ${URL}")

if [ -z "${CONTENT}" ]; then
    echo "${host_IP} ${URL}" >> /etc/hosts
    echo -n "${host_IP} ${URL} import /etc/hosts Success."
else
    echo -n "${host_IP} ${URL} is already exists."
fi
}

init_add_hosts



