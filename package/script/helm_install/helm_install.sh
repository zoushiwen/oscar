#!/usr/bin/env bash

helm_client=$1

function install_client(){

tar xf ${helm_client} -C /mnt
cd /mnt/linux-amd64 && mv helm /usr/bin
rm -rf /mnt/linux-amd64

}

function install_server(){

## 安装相关依赖包
# 初始化安装 server tiller
/usr/bin/helm init --upgrade -i registry.cn-hangzhou.aliyuncs.com/google_containers/tiller:v2.14.2 --replicas 2 \
--stable-repo-url https://kubernetes.oss-cn-hangzhou.aliyuncs.com/charts

# 创建服务账号
kubectl create serviceaccount --namespace kube-system tiller
# 创建集群的角色绑定
kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
# 为应用程序设置serviceAccount
kubectl patch deploy --namespace kube-system tiller-deploy -p '{"spec":{"template":{"spec":{"serviceAccount":"tiller"}}}}'
# 删除默认的 stable 源
helm repo remove stable
# 添加阿里云helm源
helm repo add aliyun https://kubernetes.oss-cn-hangzhou.aliyuncs.com/charts
}


install_client
install_server
