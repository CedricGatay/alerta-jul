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

from log4tailer.TermColorCodes import TermColorCodes, COLOR_YELLOW, COLOR_MAGENTA, COLOR_GREEN, COLOR_BLACK, COLOR_RED, RESET, COLOR_WHITE, COLORS

class LogColors(object):
    '''Provides the colors that will
    be used when printing Log4J levels'''

    def __init__(self):
        self.color = TermColorCodes()
        # defaults
        # color instance has dinamically assigned attributes 
        # so pylint complaints.
        # pylint: disable-msg=E1101
        self.colors = {"warning": COLORS[COLOR_YELLOW], "warn": COLORS[COLOR_YELLOW],
                       "error": COLORS[COLOR_MAGENTA], "info": COLORS[COLOR_YELLOW],
                       "fine": COLORS[COLOR_GREEN], "finer": COLORS[COLOR_GREEN],
                       "debug": COLORS[COLOR_BLACK], "config": COLORS[COLOR_BLACK],
                       "finest": COLORS[COLOR_BLACK], "fatal": COLORS[COLOR_RED],
                       "severe": COLORS[COLOR_RED], "critical": COLORS[COLOR_RED]}
        self.reset = RESET
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
        color = COLORS[COLOR_WHITE]
        if  level in self.colors.keys():
            color = self.colors[level]
        return color

