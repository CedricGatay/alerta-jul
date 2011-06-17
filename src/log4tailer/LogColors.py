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

from log4tailer.TermColorCodes import TermColorCodes
from log4tailer import LogLevels

class LogColors(object):
    '''Provides the colors that will
    be used when printing Log4J levels'''
    def __init__(self):
        self.color = TermColorCodes()
        # defaults
        # color instance has dinamically assigned attributes 
        # so pylint complaints.
        # pylint: disable-msg=E1101
        self.colors = {"warning" : self.color.yellow, "warn" : self.color.yellow,
                       "error" : self.color.magenta, "info" : self.color.yellow,
                        "fine" : self.color.green, "finer" : self.color.green,
                        "debug" : self.color.black, "config" :self.color.black,
                        "finest" : self.color.black, "fatal" : self.color.red,
                        "severe":self.color.red, "critical": self.color.red}
        self.reset = self.color.reset
        self.backgroundemph = self.color.backgroundemph

    def parse_config(self, properties):
        for (level, color) in properties.get_color_items():
            code = self.color.getCode(color)
            if not code:
                continue
            self.colors[level] = code

    def getLogColor(self, color):
        return self.color.getCode(color)
    
    def getLevelColor(self, level):
        level = level.lower()
        color = self.color.white
        if  level in self.colors.keys():
            color = self.colors[level]
        return color

