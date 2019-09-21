
from common import *

# print sudo(hostname='test1.com',cmd='mkdir /root/zoushiwen')
# print run(hostname='test1.com',cmd='ls /home')
# print run(hostname='test1.com',cmd='ls /home')


# print exec_script(hostname='test1.com',script='/Users/zoujiangtao/PycharmProjects/atom/test.sh')

# print sftp_upload(hostname='test2.com',sourceFile='package',destFile="/home/zoujiangtao/package")
#
# print exec_script(hostname='test1',script="test.sh",args="hostname",
#                   username='you_username',
#                   password='you_password'
#                   )

res = local("curl -I -m 10 -o /dev/null -s -w %{http_code}'\n'  https://10.0.0.1:8443 --insecure")
print res
