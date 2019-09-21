#!/usr/bin/env bash

NFS_PATH=$1

function install_server(){

yum -y install nfs-utils #安装
systemctl enable nfs-server #设置开机启动
systemctl start nfs-server #立即启动服务
systemctl is-active nfs-server #检查服务是否启动

if [ ! -d "${NFS_PATH}" ];then
    mkdir -p ${NFS_PATH}
fi

CONTENT=$(cat /etc/exports |grep "${NFS_PATH}")
if [ -z "${CONTENT}" ]; then
    echo "${NFS_PATH} 10.0.0.0/8(rw,sync,insecure,no_subtree_check,no_root_squash)" >> /etc/exports
    echo -n "$(hostname) import ${NFS_PATH} Success."
else
    echo -n "$(hostname) ${NFS_PATH} is already exists."
fi

systemctl reload nfs

}




install_server