#!/usr/bin/env bash



echo "hello, shell! 0130"
choice="null"
echo "${choice}"
read -p "Do you want to build dir?(yes/no): " choice
echo "${choice}"
if [ ${choice} == 'yes' ]
then
    echo "OK, we choice yes"
    mkdir we_choice_YES
else
    echo "We not choice yes..."
    mkdir we_not_choice_yes

fi