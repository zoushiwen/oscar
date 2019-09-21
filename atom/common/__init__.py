from common import Common
import subprocess
import socket

def local(cmd):
    status = subprocess.call(cmd, shell=True)
    if status == 0:
        return True
    else:
        return False

def local_run(cmd):
    p = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout,stderr = p.communicate()
    exit_code = p.returncode
    if exit_code:
        status = False
    else:
        status = True
    return {"status":status,"stdout":stdout.strip(),"stderr":stderr}


def sudo(hostname, cmd, port=None, username=None, password=None, pkey=None, timeout=None):
    try:
        common = Common(hostname=hostname, port=port, username=username, password=password,pkey=pkey,timeout=timeout)
        result = common.sudo(cmd=cmd)
        return result
    except Exception as error:
        print("{}".format(error))
        return {'status': False}

def run(hostname, cmd, port=None, username=None, password=None, pkey=None, timeout=None):
    try:
        localIP = socket.gethostbyname(socket.gethostname())
        try:
            hostnameIP = socket.gethostbyname(hostname)
            if localIP == hostnameIP:
                result = local_run(cmd=cmd)
                return {hostname:{"stdout":result['stdout'],"stderr":result['stderr']},"status":result['status']}
            else:
                common = Common(hostname=hostname, port=port, username=username, password=password, pkey=pkey,
                                timeout=timeout)
                result = common.run(cmd=cmd)
                return result
        except socket.error as error:
            print("{} {}".format(hostname, error))
    except Exception as error:
        print("{}".format(error))
        return {'status':False}

def exec_script(hostname,script,sudo=False,args=None,type=None,port=None, username=None, password=None, pkey=None,display=True,timeout=None):

    type = 'bash' if type is None else type
    try:
        localIP = socket.gethostbyname(socket.gethostname())
        try:
            hostnameIP = socket.gethostbyname(hostname)
            if localIP == hostnameIP:
                if args is None:
                    result = local_run(cmd="{} {}".format(type,script))
                else:
                    result = local_run(cmd="{} {} {}".format(type, script,args))
                return {hostname: {"stdout": result['stdout'], "stderr": result['stderr']}, "status": result['status']}
            else:
                common = Common(hostname=hostname, port=port, username=username, password=password, pkey=pkey)
                result = common.exec_script(script=script, args=args, sudo=sudo, type=type,display=display)
                return result
        except socket.error as error:
            print("{} {}".format(hostname, error))
    except Exception as error:
        print("{}".format(error))

def sftp_upload(hostname, sourceFile,destFile, port=None, username=None, password=None, pkey=None, timeout=None):
    try:
        common = Common(hostname=hostname, port=port, username=username, password=password,pkey=pkey)
        common.sftp_upload(sourceFile,destFile)
    except Exception as error:
        print("{} upload file {}".format(hostname,error.message))

def sftp_down_file(hostname, remotePath,localPath=None, port=None, username=None, password=None, pkey=None, timeout=None):
    try:
        common = Common(hostname=hostname, port=port, username=username, password=password,pkey=pkey)
        common.sftp_down_file(remotePath,localPath)
    except Exception as error:
        print("{}".format(error.message))