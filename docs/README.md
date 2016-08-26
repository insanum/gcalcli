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
Usage:

gcalcli [options] command [command args or options]

 Commands:

  list                     list all calendars

  search <text> [start] [end]            
                           search for events within an optional time period
                           - case insensitive search terms to find events that
                             match these terms in any field, like traditional
                             Google search with quotes, exclusion, etc.
                           - for example to get just games: "soccer -practice"
                           - [start] and [end] use the same formats as agenda

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
                                      --who 'boss@example.com'
                                      add

  delete <text> [start] [end]
                           delete event(s) within the optional time period
                           - case insensitive search terms to find and delete
                             events, just like the 'search' command
                           - deleting is interactive
                             use the --iamaexpert option to auto delete
                             THINK YOU'RE AN EXPERT? USE AT YOUR OWN RISK!!!
                           - use the --details options to show event details
                           - [start] and [end] use the same formats as agenda

  edit <text>              edit event(s)
                           - case insensitive search terms to find and edit
                             events, just like the 'search' command
                           - editing is interactive

  import [file]            import an ics/vcal file to a calendar
                           - a single --calendar must specified
                           - if a file is not specified then the data is read
                             from standard input
                           - if -v is given then each event in the file is
                             displayed and you're given the option to import
                             or skip it, by default everything is imported
                             quietly without any interaction
                           - if -d is given then each event in the file is
                             displayed and is not imported, a --calendar does
                             not need to be specified for this option

  remind <mins> <command>  execute command if event occurs within <mins>
                           minutes time ('%s' in <command> is replaced with
                           event start time and title text)
                           - <mins> default is 10
                           - default command:
                              'notify-send -u critical -a gcalcli %s'

 Options:

  --[no]allday: If --allday is given, the event will be an all-day event
    (possibly multi-day if --duration is greater than 1). The time part of the
    --when will be ignored.
    (default: 'false')
  --[no]cache: Execute command without using cache
    (default: 'true')
  --calendar: Which calendars to use;
    repeat this option to specify a list of values
    (default: '[]')
  --client_id: API client_id
    (default: '232867676714.apps.googleusercontent.com')
  --client_secret: API client_secret
    (default: '3tZSxItw6_VnZMezQwC8lUqy')
  --[no]color: Enable/Disable all color output
    (default: 'true')
  --color_border: Color of line borders
    (default: 'white')
  --color_date: Color for the date
    (default: 'yellow')
  --color_freebusy: Color for free/busy calendars
    (default: 'default')
  --color_now_marker: Color for the now marker
    (default: 'brightred')
  --color_owner: Color for owned calendars
    (default: 'cyan')
  --color_reader: Color for read-only calendars
    (default: 'magenta')
  --color_writer: Color for writable calendars
    (default: 'green')
  --configFolder: Optional directory to load/store all configuration information
  --[no]conky: Use Conky color codes
    (default: 'false')
  --defaultCalendar: Optional default calendar to use if no --calendar options
    are given;
    repeat this option to specify a list of values
    (default: '[]')
  --[no]default_reminders: If no --reminder is given, use the defaults. If this
    is false, do not create any reminders.
    (default: 'true')
  --description: Event description
  --[no]detail_all: Display all details
    (default: 'false')
  --[no]detail_attendees: Display event attendees
    (default: 'false')
  --[no]detail_calendar: Display calendar name
    (default: 'false')
  --[no]detail_description: Display description
    (default: 'false')
  --detail_description_width: Set description width
    (default: '80')
    (an integer)
  --[no]detail_length: Display length of event
    (default: 'false')
  --[no]detail_location: Display event location
    (default: 'false')
  --[no]detail_reminders: Display reminders
    (default: 'false')
  --detail_url: <long|short>: Set URL output
  --[no]detail_email: Display event creator's email
    (default: 'false')
  --details: Which parts to display, can be: 'all', 'calendar', 'location',
    'length', 'reminders', 'description', 'longurl', 'shorturl', 'url',
    'attendees', 'email';
    repeat this option to specify a list of values
    (default: '[]')
  -d,--[no]dump: Print events and don't import
    (default: 'false')
  --duration: Event duration in minutes or days if --allday is given.
    (an integer)
  --flagfile: Insert flag definitions from the given file into the command line.
    (default: '')
  --[no]help: Show this help
  --[no]helpshort: Show command help only
  --[no]helpxml: like --help, but generates XML output
  --[no]iamaexpert: Probably not
    (default: 'false')
  --[no]includeRc: Whether to include ~/.gcalclirc when using configFolder
    (default: 'false')
  --[no]lineart: Enable/Disable line art
    (default: 'true')
  --locale: System locale
  --[no]military: Use 24 hour display
    (default: 'false')
  --[no]monday: Start the week on Monday
    (default: 'false')
  --[no]prompt: Prompt for missing data when adding events
    (default: 'true')
  --[no]refresh: Delete and refresh cached data
    (default: 'false')
  --reminder: Reminders in the form 'TIME METH' or 'TIME'. TIME is a number
    which may be followed by an optional 'w', 'd', 'h', or 'm' (meaning weeks,
    days, hours, minutes) and default to minutes. METH is a string 'popup',
    'email', or 'sms' and defaults to popup.;
    repeat this option to specify a list of values
    (default: '[]')
  --[no]started: Show events that have started
    (default: 'true')
  --title: Event title
  --[no]tsv: Use Tab Separated Value output
    (default: 'false')
  --undefok: comma-separated list of flag names that it is okay to specify on
    the command line even if the program does not define a flag with that name.
    IMPORTANT: flags in this list that have arguments MUST use the --flag=value
    format.
    (default: '')
  --[no]use_reminders: Honour the remind time when running remind command
    (default: 'false')
  -v,--[no]verbose: Be verbose on imports
    (default: 'false')
  --[no]version: Show the version and exit
    (default: 'false')
  --when: Event time
  --where: Event location
  --who: Event attendees;
    repeat this option to specify a list of values
    (default: '[]')
  -w,--width: Set output width
    (default: '10')
    (an integer)
```

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
