gcalcli
=======

#### Google Calendar Command Line Interface

gcalcli is a Python application that allows you to access your Google
Calendar(s) from a command line. It's easy to get your agenda, search for
events, add new events, delete events, edit events, and even import those
annoying ICS/vCal invites from Microsoft Exchange and/or other sources.
Additionally, gcalcli can be used as a reminder service and execute any
application you want when an event is coming up.

Check your OS distribution for packages.

Requirements
------------

 * [Python 2](http://www.python.org)
 * [Google API Client](https://developers.google.com/api-client-library/python) Python 2 module
 * [dateutil](http://www.labix.org/python-dateutil) Python 2 module
 * [vobject](http://vobject.skyhouseconsulting.com) Python 2 module
 * [simplejson](https://github.com/simplejson/simplejson) Python 2 module
 * A love for the command line!

Features
--------

 * OAuth2 authention with your Google account
 * list your calendars
 * show an agenda using a specified start/end date and time
 * ascii text graphical calendar display with variable width
 * search for past and/or future events
 * "quick add" new events to a specified calendar
 * "add" a new event to a specified calendar (interactively or automatically)
 * "delete" event(s) from a calendar(s) (interactively or automatically)
 * "edit" event(s) interactively
 * import events from ICS/vCal files to a specified calendar
 * support for URL shortening via goo.gl
 * easy integration with your favorite mail client (attachment handler)
 * run as a cron job and execute a command for reminders
 * work against specific calendars (by calendar name w/ regex)
 * config file support for specifying option defaults
 * colored output and unicode character support
 * super fun hacking with shell scripts, cron, screen, tmux, conky, etc

Screenshots
-----------

![gcalcli](https://github.com/insanum/gcalcli/raw/master/docs/gcalcli_5.png)
![gcalcli](https://github.com/insanum/gcalcli/raw/master/docs/gcalcli_1.png)
![gcalcli](https://github.com/insanum/gcalcli/raw/master/docs/gcalcli_2.png)
![gcalcli](https://github.com/insanum/gcalcli/raw/master/docs/gcalcli_3.png)
![gcalcli](https://github.com/insanum/gcalcli/raw/master/docs/gcalcli_4.png)

HowTo
-----

#### Usage

```
gcalcli [options] command [command args]

 Options:

  --help                   this usage text

  --version                version information

  --config <file>          config file to read (default is '~/.gcalclirc')

  --cal <name>[#color]     'calendar' to work with (default is all calendars)
                           - you can specify a calendar by name or by substring
                             which can match multiple calendars
                           - you can use multiple '--cal' arguments on the
                             command line for the query commands
                           - in the config file specify multiple calendars in
                             quotes separated by commas as:
                               cal: "foo", "bar", "my cal"
                           - an optional color override can be specified per
                             calendar using the ending hashtag:
                               --cal "Eric Davis"#green --cal foo#red
                             or via the config file:
                               cal: "foo"#red, "bar"#yellow, "my cal"#green

  --24hr                   show all dates in 24 hour format

  --detail-all             show event details in the 'agenda' output
  --detail-location        - the description width defaults to 80 characters
  --detail-length          - if 'short' is specified for the url then the event
  --detail-reminders         link is shortened using http://goo.gl (slow!)
  --detail-descr           - the --detail-url can be used for both the 'quick'
  --detail-descr-width       and 'add' commands as well
  --detail-url [short,
                long]

  --ignore-started         ignore old or already started events
                           - when used with the 'agenda' command, ignore events
                             that have already started and are in-progress with
                             respect to the specified [start] time
                           - when used with the 'search' command, ignore events
                             that have already occurred and only show future
                             events

  --width                  the number of characters to use for each column in
                           the 'calw' and 'calm' command outputs (default is 10)

  --mon                    week begins with Monday for 'calw' and 'calm' command
                           outputs (default is Sunday)

  --nc                     don't use colors

  --conky                  use conky color escapes sequences instead of ansi
                           terminal color escape sequences (requires using
                           the 'execpi' command in your conkyrc)

  --cal-owner-color        specify the colors used for the calendars and dates
  --cal-writer-color       each of these argument requires a <color> argument
  --cal-reader-color       which must be one of [ default, black, brightblack,
  --cal-freebusy-color     red, brightred, green, brightgreen, yellow,
  --date-color             brightyellow, blue, brightblue, magenta,
  --now-marker-color       brightmagenta, cyan, brightcyan, white,
  --border-color           brightwhite ]

  --tsv                    tab-separated output for 'agenda'. Format is:
                           date, start, end, link, title, location, description

  --locale <locale>        set a custom locale (i.e. 'de_DE.UTF-8'). Check the
                           supported locales of your system first.

  --reminder <mins>        number of minutes to use when setting reminders for
                           the 'quick' and 'add' commands; if not specified
                           the calendar's default reminder settings are used

   --title <title>         event details used by the 'add' command
   --where <location>      - the duration is specified in minutes
   --when <datetime>       - make sure to quote strings with spaces
   --duration <#>          - datetime examples see 'agenda' below
   --descr <description>

 Commands:

  list                     list all calendars

  search <text>            search for events
                           - case insensitive search terms to find events that
                             match these terms in any field, like traditional
                             Google search with quotes, exclusion, etc.
                           - for example to get just games: "soccer -practice"

  agenda [start] [end]     get an agenda for a time period
                           - start time default is 12am today
                           - end time default is 5 days from start
                           - example time strings:
                              '9/24/2007'
                              '24/09/2007'
                              '24/9/07'
                              'Sep 24 2007 3:30pm'
                              '2007-09-24T15:30'
                              '2007-09-24T15:30-8:00'
                              '20070924T15'
                              '8am'

  calw <weeks> [start]     get a week based agenda in a nice calendar format
                           - weeks is the number of weeks to display
                           - start time default is beginning of this week
                           - note that all events for the week(s) are displayed

  calm [start]             get a month agenda in a nice calendar format
                           - start time default is the beginning of this month
                           - note that all events for the month are displayed
                             and only one month will be displayed

  quick <text>             quick add an event to a calendar
                           - a single --cal must specified
                           - the --detail-url option will show the event link
                           - example text:
                              'Dinner with Eric 7pm tomorrow'
                              '5pm 10/31 Trick or Treat'

  add                      add a detailed event to a calendar
                           - a single --cal must specified
                           - the --detail-url option will show the event link
                           - example:
                              gcalcli --cal 'Eric Davis'
                                      --title 'Analysis of Algorithms Final'
                                      --where UCI
                                      --when '12/14/2012 10:00'
                                      --duration 60
                                      --descr 'It is going to be hard!'
                                      --reminder 30
                                      add

  delete <text>            delete event(s)
                           - case insensitive search terms to find and delete
                             events, just like the 'search' command
                           - deleting is interactive
                             use the --iama-expert option to auto delete
                             THINK YOU'RE AN EXPERT? USE AT YOUR OWN RISK!!!
                           - use the --detail options to show event details

  edit <text>              edit event(s)
                           - case insensitive search terms to find and edit
                             events, just like the 'search' command
                           - editing is interactive

  import [-v] [file]       import an ics/vcal file to a calendar
                           - a single --cal must specified
                           - if a file is not specified then the data is read
                             from standard input
                           - if -v is given then each event in the file is
                             displayed and you're given the option to import
                             or skip it, by default everything is imported
                             quietly without any interaction

  remind <mins> <command>  execute command if event occurs within <mins>
                           minutes time ('%s' in <command> is replaced with
                           event start time and title text)
                           - <mins> default is 10
                           - default command:
                              'notify-send -u critical -a gcalcli %s'
```

#### Login Information

OAuth2 is used for authenticating with your Google account. The resulting token
is placed in the ~/.gcalcli_oauth file. When you first start gcalcli the
authentication process will proceed. Simply follow the instructions.

#### HTTP Proxy Support

gcalcli will automatically work with an HTTP Proxy simply by setting up some
environment variables used by the gdata Python module:

```
http_proxy
https_proxy
proxy-username or proxy_username
proxy-password or proxy_password
```

Note that these environment variables must be lowercase.

#### Config File

gcalcli is able to read default configuration information from a config file.
This file is location, by default, at '~/.gcalclirc' and must be formatted as
follows:

```
[gcalcli]
<config-option>: <value>
<config-option>: <value>
...
```

The available config items are the same as those that can be specified on the
command line.  Note that any value specified on the command line overrides the
config file.

```
cal: <name>[#color], <name>[#color], ...
24hr: <true|false>
ignore-started: <true|false>
width: <width>
mon: <true|false>
tsv: <true|false>
locale: <locale>
reminder: <minutes>
detail-all: <true|false>
detail-calendar: <true|false>
detail-location: <true|false>
detail-length: <true|false>
detail-reminders: <true|false>
detail-descr: <true|false>
detail-descr-width: <width>
detail-url: [long|short]
cal-owner-color: <color>
cal-writer-color: <color>
cal-reader-color: <color>
cal-freebusy-color: <color>
date-color: <color>
now-marker-color: <color>
border-color: <color>
```

Note that you can specify a shell command and the output will be the value for
the config variable. A shell command is determined if the first character is a
backtick (i.e. '`'). The entire command must be wrapped with backticks.

#### Importing VCS/VCAL/ICS Files from Exchange (or other)

Importing events from files is easy with gcalcli. The 'import' command accepts
a filename on the command line or can read from standard input. Here is a script
that can be used as an attachment handler for Thunderbird or in a mailcap entry
with Mutt (or in Mutt you could just use the attachment viewer and pipe command):

```
#!/bin/bash

TERMINAL=evilvte
CONFIG=~/.gcalclirc

$TERMINAL -e bash -c "echo 'Importing invite...' ; \
                      gcalcli --detail-url=short \
                              --cal='Eric Davis' \
                              import -v \"$1\" ; \
                      read -p 'press enter to exit: '"
```

Note that with Thunderbird you'll have to have the 'Show All Body Parts'
extension installed for seeing the calendar attachments when not using
'Lightning'. See this
[bug report](https://bugzilla.mozilla.org/show_bug.cgi?id=505024)
for more details.

#### Event Popup Reminders

The 'remind' command for gcalcli is used to execute any command as an event
notification. This can be a notify-send or an xmessage-like popup or whatever
else you can think of. gcalcli does not contain a daemon so you'll have to use
some other tool to ensure gcalcli is run in a timely manner for notifications.
Two options are using cron or a loop inside a shell script.

Cron:
```
% crontab -l
*/10 * * * * /usr/bin/gcalcli remind
```

Shell script like your .xinitrc so notifications only occur when you're logged
in via X:
```
#!/bin/bash

[[ -x /usr/bin/dunst ]] && /usr/bin/dunst -config ~/.dunstrc &

if [ -x /usr/bin/gcalcli ]; then 
  while true; do
    /usr/bin/gcalcli --cal="davis" remind
    sleep 300
  done &
fi

exec herbstluftwm # :-)
```

By default gcalcli executes the notify-send command for notifications. Most
common Linux desktop enviroments already contain a DBUS notification daemon
that supports libnotify so it should automagically just work. If you're like
me and use nothing that is common I highly recommend the
[dunst](https://github.com/knopwob/dunst) dmenu'ish notification daemon.

#### Agenda On Your Root Desktop

Put your agenda on your desktop using Conky. The '--conky' option causes
gcalcli to output Conky color sequences. Note that you need to use the Conky
'execpi' command for the gcalcli output to be parsed for color sequences. Add
the following to your .conkyrc:

```
${execpi 300 gcalcli --conky agenda}
```

To also get a graphical calendar that shows the next three weeks add:

```
${execpi 300 gcalcli --conky calw 3}
```

#### Agenda Integration With tmux

Put your next event in the left of your 'tmux' status line.  Add the following
to your tmux.conf file:

```
set-option -g status-interval 60
set-option -g status-left "#[fg=blue,bright]#(gcalcli agenda | head -2 | tail -1)#[default]"
```

#### Agenda Integration With screen

Put your next event in your 'screen' hardstatus line.  First add a cron job
that will dump you agenda to a text file:

```
% crontab -e
```

Then add the following line:

```
*/5 * * * * gcalcli --nc --ignore-started agenda "`date`" > /tmp/gcalcli_agenda.txt
```

Next create a simple shell script that will extract the first agenda line.
Let's call this script 'screen_agenda':

```
#!/bin/bash
head -2 /tmp/gcalcli_agenda.txt | tail -1
```

Next configure screen's hardstatus line to gather data from a backtick command.
Of course your hardstatus line is most likely very different than this (Mine
is!):

```
backtick 1 60 60 screen_agenda
hardstatus "[ %1` ]"
```

