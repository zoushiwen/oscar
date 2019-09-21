#!/bin/bash

helm del --purge harbor

kubectl delete pvc --all -n harbor
