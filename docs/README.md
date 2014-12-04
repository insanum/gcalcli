gcalcli
=======

#### Google Calendar Command Line Interface

gcalcli is a Python application that allows you to access your Google
Calendar(s) from a command line. It's easy to get your agenda, search for
events, add new events, delete events, edit events, and even import those
annoying ICS/vCal invites from Microsoft Exchange and/or other sources.
Additionally, gcalcli can be used as a reminder service and execute any
application you want when an event is coming up.

gcalcli uses the [Google Calendar API version 3](https://developers.google.com/google-apps/calendar/).

Requirements
------------

* [Python 2](http://www.python.org)
* [Google API Client](https://developers.google.com/api-client-library/python) Python 2 module
* [dateutil](http://www.labix.org/python-dateutil) Python 2 module
* [gflags](https://code.google.com/p/python-gflags/) Python 2 module
* A love for the command line!

### Optional packages

* [vobject](http://vobject.skyhouseconsulting.com) Python module  
  Used for ics/vcal importing.
* [parsedatetime](http://github.com/bear/parsedatetime) Python module  
  Used for fuzzy dates/times like "now", "today", "eod tomorrow", etc.


Installation
------------

Check your OS distribution for packages.

### Install from PyPI

```sh
pip install gcalcli
```

### Install from source

```sh
git clone https://github.com/insanum/gcalcli.git
cd gcalcli
python setup.py install
```

### Install optional packages

```sh
pip install vobject parsedatetime
```

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
 * flag file support for specifying option defaults
 * colored output and unicode character support
 * super fun hacking with shell scripts, cron, screen, tmux, conky, etc

Screenshots
-----------

![gcalcli 5](https://github.com/insanum/gcalcli/raw/master/docs/gcalcli_5.png)

![gcalcli 1](https://github.com/insanum/gcalcli/raw/master/docs/gcalcli_1.png)

![gcalcli 2](https://github.com/insanum/gcalcli/raw/master/docs/gcalcli_2.png)

![gcalcli 3](https://github.com/insanum/gcalcli/raw/master/docs/gcalcli_3.png)

![gcalcli 4](https://github.com/insanum/gcalcli/raw/master/docs/gcalcli_4.png)

HowTo
-----

#### Usage

```
gcalcli [options] command [command args]

 Options:

  --help                   this usage text

  --version                version information

  --configFolder <folder>  Folder where specific configuration information is
                           stored.  This includes a gcalclirc flags file, oauth
                           credentials, and specific cache.
  --[no]includerc          Whether the ~/.gcalclirc should be used in addition
                           to the one in the config folder

  --calendar <name>[#color]
                           'calendar' to work with (default is all calendars)
                           - you can specify a calendar by name or by substring
                             which can match multiple calendars
                           - you can use multiple '--calendar' arguments on the
                             command line for the query commands
                           - an optional color override can be specified per
                             calendar using the ending hashtag:
                               --calendar "Eric Davis"#green --calendar foo#red

  --[no]military           show all dates in 24 hour format (default = False)

  --details [all, calendar, location, length, reminders, description, url, longurl, shorturl]
                           This has the same effect as the individual switches
                           - you can specify this multiple times, to get just
                             the combination of details you want.

  --[no]detail_all           show event details in the 'agenda' output
  --[no]detail_location      - the description width defaults to 80 characters
  --[no]detail_length        - if 'short' is specified for the url then the
  --[no]detail_reminders       event link is shortened using http://goo.gl
  --[no]detail_description   - the --detail-url can be used for both the 'quick'
  --detail_url [short,         and 'add' commands as well
                long]
  --detail_description_width

  --[no]started           Show already started events (default = True)
                           - when used with the 'agenda' command, ignore events
                             that have already started and are in-progress with
                             respect to the specified [start] time
                           - when used with the 'search' command, ignore events
                             that have already occurred and only show future
                             events

  --width                  the number of characters to use for each column in
                           the 'calw' and 'calm' command outputs (default is 10)

  --[no]monday             week begins with Monday for 'calw' and 'calm' command
                           outputs (default is False meaning Sunday)

  --[no]colors             Use colors (defalt = True)

  --[no]lineart            Use line graphics (default = True)

  --[no]conky              use conky color escapes sequences instead of ansi
                           terminal color escape sequences (requires using
                           the 'execpi' command in conkyrc) (default = False)

  --color_owner            specify the colors used for the calendars and dates
  --color_writer           each of these argument requires a <color> argument
  --color_reader           which must be one of [ default, black, brightblack,
  --color_freebusy             red, brightred, green, brightgreen, yellow,
  --color_date                 brightyellow, blue, brightblue, magenta,
  --color_now_marker           brightmagenta, cyan, brightcyan, white,
  --color_border               brightwhite ]

  --[no]tsv                tab-separated output for 'agenda'. Format is:
                           start date, start time, end date, end time, link, title, location, description
                           (default = False)

  --locale <locale>        set a custom locale (i.e. 'de_DE.UTF-8'). Check the
                           supported locales of your system first.

  --reminder <mins>        number of minutes to use when setting reminders for
                           the 'quick' and 'add' commands; if not specified
                           the calendar's default reminder settings are used

  --title <title>          event details used by the 'add' command
  --where <location>       - the duration is specified in minutes
  --when <datetime>        - make sure to quote strings with spaces
  --duration <#>           - datetime examples see 'agenda' below
  --description <descr>
  --[no]prompt             Whether we should prompt for any missing pieces of
                           data when doing an add. (Default = True)

  --[no]refresh            Force a refresh of cached data (Default = False)

  --[no]cache              Use cached data (Default = True)

  --[no]verbose            Output data on each event when importing from an ics
                           file

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
                           - a single --calendar must specified
                           - the "--details url" option will show the event link
                           - example text:
                              'Dinner with Eric 7pm tomorrow'
                              '5pm 10/31 Trick or Treat'

  add                      add a detailed event to a calendar
                           - a single --calendar must specified
                           - the "--details url" option will show the event link
                           - example:
                              gcalcli --calendar 'Eric Davis'
                                      --title 'Analysis of Algorithms Final'
                                      --where UCI
                                      --when '12/14/2012 10:00'
                                      --duration 60
                                      --description 'It is going to be hard!'
                                      --reminder 30
                                      add

  delete <text>            delete event(s)
                           - case insensitive search terms to find and delete
                             events, just like the 'search' command
                           - deleting is interactive
                             use the --iamaexpert option to auto delete
                             THINK YOU'RE AN EXPERT? USE AT YOUR OWN RISK!!!
                           - use the --details options to show event details

  edit <text>              edit event(s)
                           - case insensitive search terms to find and edit
                             events, just like the 'search' command
                           - editing is interactive

  import [-v|-d] [file]    import an ics/vcal file to a calendar
                           - a single --calendar must specified
                           - if a file is not specified then the data is read
                             from standard input
                           - if -v is given then each event in the file is
                             displayed and you're given the option to import
                             or skip it, by default everything is imported
                             quietly without any interaction
                           - if -d is given then each event in the file is
                             displayed and not imported, a --calendar does
                             not need to be specified for this option

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

#### Flag File

gcalcli is able to read default configuration information from a flag file.
This file is located, by default, at '~/.gcalclirc'.  The flag file takes one
command line parameter per line.

Example:

```
--military
--duration=55
--details=calendar
--details=location
--details=length
-w 10
```

Note that long options require an equal sign if specifying a parameter.  With
short options the equal sign is optional.

#### Configuration Folders

gcalcli is able to store all its necessary information in a specific folder (use
the --configFolder option.) Each folder will contain 2 files: oauth and cache.
An optional 3rd file, gcalclirc, can be present for specific flags that you only
want to apply when using this configuration folder.

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
                              --calendar='Eric Davis' \
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
    /usr/bin/gcalcli --calendar="davis" remind
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

You may need to increase the `text_buffer_size` in your conkyrc file.  Users
have reported that the default of 256 bytes is too small for busy calendars.

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
*/5 * * * * gcalcli --nocolor --nostarted agenda "`date`" > /tmp/gcalcli_agenda.txt
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
