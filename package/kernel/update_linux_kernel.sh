#!/usr/bin/env bash



green='\e[1;32m' # green
red='\e[1;31m' # red
blue='\e[1;34m' # blue
nc='\e[0m' # normal

function update_linux_kernel() {
    kernel_path=$(cd `dirname $0`; pwd)
    echo ${kernel_path}
#    kernel_lt='kernel-lt-4.4.177-1.el7.elrepo.x86_64.rpm'
#    kernel_lt_devel='kernel-lt-devel-4.4.177-1.el7.elrepo.x86_64.rpm'
    # 下载 linux kernel 安装包
    \cp -f ${kernel_path}/RPM-GPG-KEY-elrepo.org /etc/pki/rpm-gpg/
    yum localinstall -y ${kernel_path}/*.rpm
    i=$?
    if [ $i == 0 ];then
		echo -e "[${green}${kernel_path}/*.rpm Install Success${nc}]"
	else
		echo -e "[${red}$@ Install Failed${nc}]"
		echo "Please check your config.."
		exit 3
	fi
    cat /boot/grub2/grub.cfg | grep menuentry >/dev/null 2>&1
    grub2-set-default 'CentOS Linux (4.4.177-1.el7.elrepo.x86_64) 7 (Core)'

}

update_linux_kernel