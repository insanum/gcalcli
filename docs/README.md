gcalcli
=======

#### Google Calendar Command Line Interface

gcalcli is a Python application that allows you to access your Google
Calendar(s) from a command line. It's easy to get your agenda, search for
events, quickly add new events, and even import those annoying vCal invites
from Microsoft Exchange. Additionally, gcalcli can be used as a reminder
service to execute any application you want.

Check your OS Distribution for packages.

Requirements
------------

 * [Python 2](http://www.python.org)
 * Google's [GData](http://code.google.com/p/gdata-python-client) Python 2 module
 * [dateutil](http://www.labix.org/python-dateutil) Python module
 * [vobject](http://vobject.skyhouseconsulting.com) Python module
 * A love for the command line!

Features
--------

 * list your calendars
 * show an agenda using a specified start/end date and time
 * graphical calendar display with variable width
 * search for past and/or future calendar events
 * "quick add" new events to a specified calendar
 * import ics/vcal files to a specified calendar
 * run as a cron job and execute a command for reminders
 * work against specific calendars (by calendar type or calendar name regex)
 * config file support for specifying option defaults
 * colored output and unicode character support
 * easy within shell scripts, cron, screen, tmux, conky, etc

Screenshots
-----------

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

  --user <username>        google username

  --pw <password>          password

  --cals [all,             'calendars' to work with (default is all calendars)
          default,         - default (your default main calendar)
          owner,           - owner (your owned calendars)
          editor,          - editor (editable calendar)
          contributor,     - contributor (non-owner but able to edit)
          read,            - read (read only calendars)
          freebusy]        - freebusy (only free/busy info visible)

  --cal <name>[#color]     'calendar' to work with (default is all calendars)
                           - you can specify a calendar by name or by substring
                             which can match multiple calendars
                           - you can use multiple '--cal' arguments on the
                             command line
                           - in the config file specify multiple calendars in
                             quotes separated by commas as:
                               cal: "foo", "bar", "my cal"
                           - an optional color override can be specified per
                             calendar using the ending hashtag:
                               --cal "Eric Davis"#green --cal foo#red
                             or via the config file:
                               cal: "foo"#red, "bar"#yellow, "my cal"#green

  --24hr                   show all dates in 24 hour format

  --details                show all event details (i.e. length, location,
                           reminders, contents)

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

  --cal-owner-color        specify the colors used for the calendars and dates
  --cal-editor-color       each of these argument requires a <color> argument
  --cal-contributor-color  which must be one of [ default, black, brightblack,
  --cal-read-color         red, brightred, green, brightgreen, yellow,
  --cal-freebusy-color     brightyellow, blue, brightblue, magenta,
  --date-color             brightmagenta, cyan, brightcyan, white,
  --border-color           brightwhite ]

  --tsv                    tab-separated output for 'agenda'. Format is:
                           'date' 'start' 'end' 'title' 'location' 'description'

  --locale                 set a custom locale (i.e. 'de_DE.UTF-8'). Check the
                           supported locales of your system first.

 Commands:

  list                     list all calendars

  search <text>            search for events
                           - only matches whole words

  agenda [start] [end]     get an agenda for a time period
                           - start time default is 12am today
                           - end time default is 5 days from start
                           - example time strings:
                              '9/24/2007'
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
                           - if a --cal is not specified then the event is
                             added to the default calendar
                           - example:
                              'Dinner with Eric 7pm tomorrow'
                              '5pm 10/31 Trick or Treat'

  import [-v] [file]       import an ics/vcal file to a calendar
                           - if a --cal is not specified then the event is
                             added to the default calendar
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
                              'gxmessage -display :0 -center \
                                         -title "Ding, Ding, Ding!" %s'
```

#### Login Information

You can provide gcalcli with your Google Calendar login information via one of
the following:

 * on the command line using the --user and --pw options
 * the config file
 * or interactively when prompted

In any case make sure you protect the information.

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
user: <username>
pw: <password>
cals: <type>
cal: <name>[#color], <name>[#color], ...
24hr: <true|false>
details: <true|false>
ignore-started: <true|false>
width: <width>
mon: <true|false>
nd: <true|false>
cal-owner-color: <color>
cal-editor-color: <color>
cal-contributor-color: <color>
cal-read-color: <color>
cal-freebusy-color: <color>
date-color: <color>
border-color: <color>
locale: <locale>
```

Note that you can specify a shell command and the output will be the value for
the config variable. A shell command is determined if the first character is a
backtick (i.e. '`'). An example is pulling a password from gpg:

```
pw: `gpg --decrypt ~/mypw.gpg`
```

#### Event Popup Reminders Using Cron

Run gcalcli using cron and generate xmessage-like popups for reminders.

```
% crontab -e
```

Then add the following line:

```
*/10 * * * * gcalcli remind
```

#### Agenda On Your Root Desktop

Put your agenda on your desktop using Conky. Add the following to your
.conkyrc:

```
${execi 300 gcalcli --nc agenda}
```

To also get a graphical calendar that shows the next three weeks add:

```
${execi 300 gcalcli --nc --cals=owner calw 3}
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

