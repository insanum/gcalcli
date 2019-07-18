gcalcli
=======
[![Build Status](https://travis-ci.org/insanum/gcalcli.svg?branch=master)](https://travis-ci.org/insanum/gcalcli)

#### Google Calendar Command Line Interface

gcalcli is a Python application that allows you to access your Google
Calendar(s) from a command line. It's easy to get your agenda, search for
events, add new events, delete events, edit events, see recently updated 
events, and even import those annoying ICS/vCal invites from Microsoft 
Exchange and/or other sources. Additionally, gcalcli can be used as a reminder
service and execute any application you want when an event is coming up.

gcalcli uses the [Google Calendar API version 3](https://developers.google.com/google-apps/calendar/).

Requirements
------------

* [Python](http://www.python.org) (2.7, 3+)
* [dateutil](http://www.labix.org/python-dateutil)
* [Google API Client](https://developers.google.com/api-client-library/python)
* [httplib2](https://github.com/httplib2/httplib2)
* [oauth2client](https://github.com/google/oauth2client)
* [six](https://pythonhosted.org/six/)
* [parsedatetime](https://github.com/bear/parsedatetime)
* A love for the command line!

### Optional packages

* [vobject](http://vobject.skyhouseconsulting.com) Python module
  Used for ics/vcal importing.

Installation
------------

Check your OS distribution for packages.

### Debian/Ubuntu

```sh
apt-get install gcalcli
```

### Install using [Nix](https://nixos.org/nix/)

```sh
nix-env -i gcalcli
```

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

### Install optional package

```sh
pip install vobject
```

Features
--------

 * OAuth2 authention with your Google account
 * list your calendars
 * show an agenda using a specified start/end date and time
 * show updates since a specified datetime for events between a start/end date and time
 * ascii text graphical calendar display with variable width
 * search for past and/or future events
 * "quick add" new events to a specified calendar
 * "add" a new event to a specified calendar (interactively or automatically)
 * "delete" event(s) from a calendar(s) (interactively or automatically)
 * "edit" event(s) interactively
 * import events from ICS/vCal files to a specified calendar
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

`gcalcli` provides a series of subcommands with the following functionality:

    list                list available calendars
    edit                edit calendar events
    agenda              get an agenda for a time period
    updates             get updates since a datetime for a time period
    calw                get a week-based agenda in calendar format
    calm                get a month agenda in calendar format
    quick               quick-add an event to a calendar
    add                 add a detailed event to the calendar
    import              import an ics/vcal file to a calendar
    remind              execute command if event occurs within <mins> time

See the manual (`man (1) gcalcli`), or run with `--help`/`-h` for detailed usage.

#### Login Information

OAuth2 is used for authenticating with your Google account. The resulting token
is placed in the ~/.gcalcli_oauth file. When you first start gcalcli the
authentication process will proceed. Simply follow the instructions.

If desired, you can use your own Calendar API instead of the default API values.
*NOTE*: these steps are optional!

* Go to the [Google developer console](https://console.developers.google.com/)
* Make a new project for gcalcli
* On the sidebar under APIs & Auth, click APIs
* Enable the Calendar API
* On the sidebar click Credentials
* Create a new Client ID. Set the type to Installed Application and the subtype
  to Other. You will be asked to fill in some consent form information, but what
  you put here isn't important. It's just what will show up when gcalcli opens
  up the OAuth website. Anything optional can safely be left blank.
* Go back to the credentials page and grab your ID and Secret.
* If desired, add the client_id and client_secret to your .gcalclirc:

        --client_id=xxxxxxxxxxxxxxx.apps.googleusercontent.com
        --client_secret=xxxxxxxxxxxxxxxxx

* Remove your existing OAuth information (typically ~/.gcalcli_oauth).
* Run gcalcli with any desired argument, making sure the new client_id and
  client_secret are passed on the command line or placed in your .gcalclirc. The
  OAuth authorization page should be opened automatically in your default
  browser.

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

`gcalcli` is able to read default configuration information from a flag file.
This file is located, by default, at '~/.gcalclirc'.  The flag file takes one
command line parameter per line.

In the current version, the flag file only supports the global options (options
against the `gcalcli` program itself).  The plan, longer term, is to support a
a configuration formation (probably toml or ini), which will allow for
configuration of subcommands (such as `add`, `agenda`, `calw`, etc.)

Example:

```
--nocache
--nocolor
--default-calendar=CALENDAR_NAME
--client-secret=API_KEY
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

```sh
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
```sh
% crontab -l
*/10 * * * * /usr/bin/gcalcli remind
```

Shell script like your .xinitrc so notifications only occur when you're logged
in via X:
```sh
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

Note that each time you run this you will get a reminder if you're still inside
the event duration.  Also note that due to time slip between machines, gcalcli
will give you a ~5 minute margin of error.  Plan your cron jobs accordingly.

#### Agenda On Your Root Desktop

Put your agenda on your desktop using
[Conky](https://github.com/brndnmtthws/conky). The '--conky' option causes
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

Additionaly you need to set `--lineart=unicode` to output unicode-characters
for box drawing. To avoid misaligned borders use a monospace font like 'DejaVu
Sans Mono'. On Python2 it might be necessary to set the environment variable
`PYTHONIOENCODING=utf8` if you are using characters beyond ascii. For
example:
```
${font DejaVu Sans Mono:size=9}${execpi 300 export PYTHONIOENCODING=utf8 && gcalcli --conky --lineart=unicode calw 3}
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
