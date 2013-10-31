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
* A love for the command line!

### Optional packages
* [vobject](http://vobject.skyhouseconsulting.com) Python module

    Used for ics/vcal importing.

* [parsedatetime](http://github.com/bear/parsedatetime) Python module

    Used for fuzzy dates/times like "now", "today", "eod tomorrow", etc.

Screenshots
-----------

See `docs/README.md`

![gcalcli](https://github.com/insanum/gcalcli/raw/master/docs/gcalcli_4.png)

Install with package Manager
----------------------------

* Install it in your favorite distro (`apt-get install gcalcli`, ...)

* `cp .gcalclirc.sample .gcalclirc` # and edit it!

* Use: `gcalcli agenda`

Enjoy! For more on how to use it, see docs in `docs/`

Install on github
-----------------

```
 $ git clone git://github.com/insanum/gcalcli.git gcalcli/
 $ cp gcalcli/.gcalcli.sample ~/.gcalcli
 $ gcalcli/gcalcli agenda
