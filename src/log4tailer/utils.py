# Log4Tailer: A multicolored python tailer for log4J logs
# Copyright (C) 2008 Jordi Carrillo Bosch

# This file is part of Log4Tailer Project.
#
# Log4Tailer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Log4Tailer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Log4Tailer.  If not, see <http://www.gnu.org/licenses/>.

from time import localtime, strftime
import getpass
from log4tailer import notifications
import os
import sys

def setup_mail(properties):
    username = properties.get_value("mail_username")
    hostname = properties.get_value("mail_hostname")
    port = properties.get_value("mail_port") or 25
    ssl = properties.get_value("mail_ssl")
    mail_from = properties.get_value("mail_from")
    mail_to = properties.get_value("mail_to")
    password = getpass.getpass()
    mailAction = notifications.Mail(mail_from, mail_to, hostname, username,
            password, port, ssl) 
    mailAction.connectSMTP()
    return mailAction

def get_now():
    return strftime("%d %b %Y %H:%M:%S", localtime())

def hours_mins_format(secs):
    years, secs = divmod(secs, 31556926)
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    days, hours = divmod(hours, 24)
    return (str(years) + " years " + str(days) + " days " + str(hours) +
            " hours " + str(mins) + " mins " + str(secs) + " secs ")

def daemonize (stdin='/dev/null', stdout='/dev/null', 
        stderr='/dev/null'):
    try:
        pid = os.fork( )
        if pid > 0:
            sys.exit(0) 
    except OSError, e:
        sys.stderr.write("first fork failed: (%d) %s\n" % (e.errno, 
            e.strerror))
        sys.exit(1)
    os.chdir("/")
    os.umask(0)
    os.setsid( )
    try:
        pid = os.fork( )
        if pid > 0:
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("second fork failed: (%d) %s\n" % (e.errno, 
            e.strerror))
        sys.exit(1)
    print "daemonized"
    for f in sys.stdout, sys.stderr: f.flush()
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())


