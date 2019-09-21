# -*- coding: utf-8 -*-
import os

import sys
import os.path

if sys.version_info[:3][0] == 2:
    import ConfigParser as ConfigParser
if sys.version_info[:3][0] == 3:
    import configparser as ConfigParser

def config():

    baseDir = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
    cfg = ConfigParser.ConfigParser()
    confFile = os.path.join(baseDir,'config.ini')
    cfg.read(confFile)
    return cfg

class DefaultOption(dict):
    """
    给配置文件设置默认值
    """

    def __init__(self, config, section, **kv):
        self._config = config
        self._section = section
        dict.__init__(self, **kv)

    # def items(self):
    #     _items = []
    #     for option in self:
    #         if not self._config.has_option(self._section, option):
    #             _items.append((option, self[option]))
    #         else:
    #             value_in_config = self._config.get(self._section, option)
    #             _items.append((option, value_in_config))
    #     return _items
    def configDict(self):
        _items = dict()
        for option in self:
            if not self._config.has_option(self._section, option):
                _items.update({option:self[option]})
            else:
                value_in_config = self._config.get(self._section, option)
                _items.update({option:value_in_config})
        return _items

class GetBaseconfig:
    """

    NODE_HOST: node host 列表节点的机器名

    """
    cfg = config()
    MASTER = cfg.items("master")
    NODE = cfg.items("node")
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    LOG_FILE = DefaultOption(cfg, "default", log_file="/var/log/k8s.log").configDict()['log_file']
    PACKAGE_DIR = os.path.join(BASE_DIR,"package")
    MASTER_HOST = [masterHostname for master, masterHostname in MASTER]
    NODE_HOST = [nodeHostname for node, nodeHostname in NODE]




# if __name__ == '__main__':
#     cfg = config()

