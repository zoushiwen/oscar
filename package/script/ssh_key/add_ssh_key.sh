#!/usr/bin/env bash

hostname=$1
authorized_keys=$2
id_rsa_pub=$3


function init() {

mkdir -p /root/.ssh
if [ ! -f "${authorized_keys}" ];then
    touch ${authorized_keys}
fi
# 导入ssh key 密钥
CONTENT=$(cat ${authorized_keys} |grep ${hostname})
if [ -z "${CONTENT}" ]; then
    echo ${id_rsa_pub} >> ${authorized_keys}
    echo -n "${hostname} import ssh key Success."
else
    echo -n "${hostname} is already exists."
fi

## 公司环境 开启root登陆
SSH_CONTENT=$(grep 'PermitRootLogin yes' /etc/ssh/sshd_config)
if [ -z "${SSH_CONTENT}" ];then
    sed -i "s/PermitRootLogin no/#PermitRootLogin yes/g" /etc/ssh/sshd_config
    systemctl restart sshd
    echo "root has been launched."
fi
}

init