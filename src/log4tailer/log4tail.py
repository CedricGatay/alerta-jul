#!/usr/bin/env python 

# Log4Tailer: A multicolored python tailer for log4J logs
# Copyright (C) 2008 Jordi Carrillo Bosch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys

from optparse import OptionParser
import log4tailer

def startupNotice():
    notice = """Log4Tailer  Copyright (C) 2008 Jordi Bosch
        This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.
            This is free software, and you are welcome to redistribute it
                under certain conditions; type `show c' for details."""
    print notice           

def parse_command_line():
    if len(sys.argv[1:]) == 0:
        print "Provide at least one log"
        sys.exit()
    parser = OptionParser()
    parser.add_option("-c", "--config", dest="configfile",
            help="config file with colors")
    parser.add_option("-p", "--pause", dest="pause", 
            help="pause between tails")
    parser.add_option("--throttle", dest="throttle",
            help="throttle output, slowsdown")
    parser.add_option("-i", "--inact", dest="inactivity",
            help="monitors inactivity in log given inactivity seconds")
    parser.add_option("-s", "--silence", action="store_true", dest="silence",
            help="tails in silence, no printing")
    parser.add_option("-n", dest="tailnlines",
            help="prints last N lines from log")
    parser.add_option("-t", "--target", dest="target",
            help="emphasizes a line in the log")
    parser.add_option("-m","--mail", action="store_true", dest="mail",
            help="notification by mail when a fatal is found")
    parser.add_option("-r","--remote", action="store_true", dest="remote",
            help="remote tailing over ssh")
    parser.add_option("-f", "--filter", dest="filter",
            help="filters log traces, tail and grep")
    parser.add_option("--cornermark", dest="cornermark",
            help="displays a mark in bottom right corner of terminal")
    parser.add_option("--no-mail-silence", action="store_true", 
            dest="nomailsilence", help="silent mode but no specific notification")
    parser.add_option("--executable", action="store_true", 
            dest="executable", help="executes a program")
    parser.add_option("--version", action="store_true", 
            dest="version", help="shows log4tailer version number and exists")
    parser.add_option("--post", action="store_true", dest="post", 
        help="sends http alert to a centralized web server")
    parser.add_option("--screenshot", action="store_true", dest="screenshot", 
        help="takes a terminal screenshot whenever it finds an alertable log "
                "trace")
 
    return parser.parse_args()

def main():
    options, args = parse_command_line()
    log4tailer.main(options, args)

if __name__ == '__main__':
    main()

