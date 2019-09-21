### Description

- k8s一键安装脚本系统----在线环境安装
   
    
### System
 
 - CentOS 7

### Version
- k8s v1.15.0 默认最新版本
- docker 阿里云的yum仓库
- kubernetes 阿里云的yum参考
- kubeadm 镜像阿里云的公有镜像仓库
 
### 功能

 - 单集群部署一主多从
 - HA可用集群部署（keepalived + Haproxy 高可用方案）
 - 自动升级Linux内核版本
 



### Usage

#### 1.安装依赖包

~~~
[root@q12469v oscar]# yum install -y python-paramiko 
~~~

#### 2. 修改配置文件 config.ini

~~~
[ha]
VIP = ${VIP}   ; 为安装机器的ip地址

[master]
MASTER0 =  ${master0_hostname} ;一般安装选择第一台master机器作为k8s集群安装
MASTER1 =  ${master1_hostname}
MASTER2 =  ${master2_hostname}

[node]
NODE1 = ${node1_hostname} ；需要填写 node 的hostname
NODE2 = ${node2_hsotname}

...

# 获取VIP (假设网卡在eth0),VIP需要指定为IP地址
[root@q12469v oscar]# ifconfig eth0 |grep inet|grep -v 127.0.0.1|grep -v inet6|awk '{print $2}'|tr -d "addr:"
提示：  
    1、mater 和 node 在公司环境，需要指定为机器的hostname，不要指定机器ip地址 
  
~~~

#### 3. 机器ssh密钥认证

~~~
 # 指定的用户名和密码是能访问整个k8s集群登陆机器账号                                 
[root@q12469v oscar]# python oscar.py -m add_ssh_key -u 'you_username' -p 'you_password'

# ssh key 密钥认证工具，

-u [USERNAME], --username [USERNAME]
                        Enter the login machine username.
-p [PASSWORD], --password [PASSWORD]
                        Enter the login machine password.
                        
注意：假如指定的为非root用户，需要提供用户('you_username')有sudo权限   
oscar 默认用的是 root 用户的密钥认证的安装的  

~~~

#### 4.升级内核

~~~
# master 因为ipvs 内核版本需要不低于 4.19，如果低于Oscar会升级内核，内核升级完成之后会提示重启机器
[root@q12469v oscar]# python oscar.py -m update -a linux_kernel

~~~

#### 5. 安装k8s集群

~~~ 
# 也可以查看帮组信息
[root@q12469v oscar]# python oscar.py -h

# HA 安装整个k8s集群,需要指定三个 master 节点
[root@q12469v oscar]# python oscar.py -m install -a k8s

~~~

#### 6 安装 ingress (如果需要的话，额外插件)

~~~

[root@q12469v oscar]# python oscar.py -m install -a ingress

~~~

### 支持安装插件

- helm
- nfs
- gitlab
- harbor
- rbd

~~~
# 安装插件 helm
[root@q12469v oscar]# python oscar.py -m install -a helm

# 安装插件 nfs 需要修改配置文件 config.ini
nfsServer = ${nfsServer_Ip} ；需要选择一台nfs机器作为k8s集群的nfs存储，比如选择 NODE1节点，把nfsServer_Ip修改为NODE1的IP地址即可
nfsPath = /nfs/k8s  ；存放pvc目录，可以不修改
[root@q12469v oscar]# python oscar.py -m install -a nfs

# 安装 gitlab 需要修改默认配置文件 config.ini
[gitlab]
externalUrl = http://${url}
# 然后执行安装，访问用户名为 root 密码为config.ini文件中 ${gitlabRootPassword}
[root@q12469v oscar]# python oscar.py -m install -a gitlab
# 删除 gitlab
[root@q12469v oscar]# python oscar.py -m delete -d gitlab

~~~


#### 安装 harbor 需要修改默认配置文件 config.ini
~~~
[harbor]
externalURL = https://${url_hosts}
### 然后执行安装 harbor，安装成功后，可以访问 https://${url_hosts};访问用户名为admin 密码为配置文件中 ${harborAdminPassword}
[root@q12469v oscar]# python oscar.py -m install -a harbor
### 删除 harbor
[root@q12469v oscar]# python oscar.py -m delete -d harbor

~~~
>  如果推送镜像的机器在k8s集群中，在安装的`harbor`，会自动在各个k8s节点 `/etc/docker/daemon.json` 添加 `"insecure-registries":[${url_hosts}]` 只需重启 docker 即可上传镜像

```
systemctl daemon-reload
systemctl restart docker.service

```

#### 往`harobr`推送`docker`镜像，推送节点不在k8s节点中

`docker push`命令推送镜像时默认采用了`https`协议,查看config.ini 配置文件中${url_hosts}值
```
vim /etc/docker/daemon.json 添加
{
    "insecure-registries":[${url_hosts}]
}
```

如果没有上面的操作，那么推送docker logiin时会遇到类似下面的错，

```
Error response from daemon: Get http://${url_hosts}/v2/: dial tcp ${url_hosts}:80: getsockopt: connection refused
```

可以参考该链接：https://docs.docker.com/registry/insecure  了解详细信息。

重启docker服务:

```
systemctl daemon-reload
systemctl restart docker.service
```

客户端在推送镜像之前需要先登录，比如：

```
docker login $${url_hosts} -u admin -p Harbor12345
```

然后给要推送的镜像打标签：

```
docker image tag fce289e99eb9  ${url_hosts}/library/test:latest
```

推送镜像：

```
docker image push ${url_hosts}/library/test:latest
```

ok，现在打开浏览器`harbor`仓库页面，如果有你刚刚推送的镜像，那么`harbor`部署就成功了。






