# -*- coding:utf-8 -*-

from utils.tools import Print,Utils
import os
from utils.config import GetBaseconfig
from atom.common import *

base_dir = GetBaseconfig.BASE_DIR
LOG_FILE = GetBaseconfig.LOG_FILE
MASTER_HOST = GetBaseconfig.MASTER_HOST

K8S_DEST_DIR = Utils.getUserInstallHome()
kernel_dir = os.path.join(base_dir, "package/kernel")


class Kernel:

    def __init__(self):

        self.local_master = socket.gethostname()
        self.other_master = [ master for master in MASTER_HOST if master not in socket.gethostname()]


    def other_kernel(self):
        for hostname in self.other_master:
            res = run(hostname, "uname -r")
            if res['status']:
                kernel = res[hostname]['stdout'].strip()
            else:
                kernel = None
                Print("{} Failed to get the kernel version".format(hostname), colour="red")
            kernel_short = float(kernel[0:3])
            if kernel_short < float(4.19):
                Print("{} kernel version {},Need to upgrade the kernel".format(hostname, kernel), colour="green")
                result = self.update_linux_kernel(hostname)
                if result:
                    sudo(hostname=hostname, cmd="reboot")
            else:
                Print("{} kernel version {}".format(hostname, kernel), colour="green")

    def local_kernel(self):
        res = subprocess.Popen("uname -r", shell=True, stdout=subprocess.PIPE)
        kernel = res.stdout.read().strip()
        kernel_short = float(kernel[0:3])
        if kernel_short < float(4.19):
            Print("{} kernel version {},Need to upgrade the kernel".format(self.local_master, kernel), colour="green")
            self.update_linux_kernel(self.local_master)
            reboot_status = raw_input("[execute [reboot machine] ?( yes/no)] ")
            if reboot_status == "yes":
                local(cmd="reboot")
        else:
            Print("{} kernel version {}".format(self.local_master, kernel), colour="green")



    def update_linux_kernel(self,hostname):
            # 升级Linux内核
            print("{} staring update linux kernel".format(hostname))
            ip_result = Utils.localCMPHostname(hostname)
            if ip_result:
                local_update_linux_script = os.path.join(kernel_dir, "update_linux_kernel.sh")
                result_script = local("bash {}".format(local_update_linux_script))
                if result_script:
                    Print("Please restart {} later".format(hostname),colour="yellow")
                else:
                    Print("update kernel failed",colour="red")
            else:
                remote_update_linux_script = os.path.join(K8S_DEST_DIR, 'update_linux_kernel.sh')
                sftp_upload(hostname,kernel_dir,K8S_DEST_DIR)
                Print("Kernel is being upgraded, please wait a moment.",hostname=hostname,colour="green")
                result_script = sudo(hostname,"bash {}".format(remote_update_linux_script))
                print(result_script[hostname]['stdout'])
                if result_script['status']:
                    # reboot_status = raw_input("[execute [reboot machine] ?( yes/no)] ")
                    # if reboot_status == "yes":

                    Print("{} will be restarted soon".format(hostname),colour="yellow")
                    return True
                        # sys.exit(1)
                else:
                    Print("{} exec update_linux_kernel.sh False.",colour="red")
                    return False

