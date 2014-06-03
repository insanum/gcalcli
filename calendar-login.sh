#!/bin/bash
username=$1
password=$2

echo "Trying to login with user $username and password $password"

if [ ! -e cookies.txt ]
then
	wget --save-cookies=cookies.txt http://compiere2/calendar/login.php --post-data="login=$username&password=$password&remember=yes" -O /dev/null
fi

