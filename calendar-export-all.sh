#!/bin/bash

if [ ! -e cookies.txt ]
then
	./calendar-login.sh
fi

wget http://compiere2/calendar/export_handler.php --post-data="use_all_dates=y&format=ical" --load-cookies=cookies.txt -O export.ical

