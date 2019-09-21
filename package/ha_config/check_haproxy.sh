#!/bin/bash

check_haproxy=$(ps -C haproxy --no-header |wc -l)

if [ $check_haproxy -eq 0 ];then
    systemctl status keepalived
fi