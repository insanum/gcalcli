# Maintainer: Gabriel Fornaeus <gf@hax0r.se>
# Contributor: Gabriel Fornaeus <gf@hax0r.se>

pkgname=gcalcli-archlinux-git
pkgver=20140816.3
pkgrel=1
pkgdesc="Allows you to access you Google Calendar from a command line, git version, updated specifically for Arch"
arch=('i686' 'x86_64')
url="https://github.com/stratosmacker/gcalcli-archlinux.git"
license=('MIT')
depends=('python2-dateutil' 'python2-httplib2'
'python2-google-api-python-client' 'python2-gdata' 'python2-gflags')
optdepends=('python2-vobject: used for ics/vcal importing'
'python2-parsedatetime: used for fuzzy dates/times like "now",
"today", "eod tomorrow", etc.')
makedepends=('git')
makedepends=('git')
provides=('gcalcli')
conflicts=('gcalcli')

_gitroot="https://github.com/stratosmacker/gcalcli-archlinux.git"
_gitname="gcalcli-archlinux-git"

build() {
    cd ${srcdir}

    msg "Connecting to GIT server..."
    if [[ -d ${_gitname} ]]; then
        (cd ${_gitname} && git pull origin)
    else
        git clone ${_gitroot} ${_gitname}
    fi
    msg "GIT checkout done or server timeout"
    msg "Starting build"
    cd ${_gitname}
    install -D -m755 gcalcli ${pkgdir}/usr/bin/gcalcli
    install -D -m755 calendar-export-all.sh ${pkgdir}/usr/bin/calendar-export-all.sh
    install -D -m755 calendar-login.sh ${pkgdir}/usr/bin/calendar-login.sh
    install -D -m644 .gcalclirc.sample ${pkgdir}/etc/gcalcli/gcalclirc
}
