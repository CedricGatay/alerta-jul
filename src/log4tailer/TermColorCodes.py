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


# some code taken from termcolor GPL module in pypi by 
# Konstantin Lepa <konstantin.lepa@gmail.com>

COLORS = dict(
        zip([
            'black',
            'red',
            'green',
            'yellow',
            'blue',
            'magenta',
            'cyan',
            'white',
            ],
            range(30, 38)
            )
        )

HIGHLIGHTS = dict(
        zip([
            'on_black',
            'on_red',
            'on_green',
            'on_yellow',
            'on_blue',
            'on_magenta',
            'on_cyan',
            'on_white'
            ],
            range(40, 48)
            )
        )

SUFFIX_CODE ='\033[%dm'
RESET = '\033[0m'

class TermColorCodes:
    '''Defines the ANSI Terminal
    color codes'''
    def __init__(self):
        for k in COLORS:
            setattr(self, k, SUFFIX_CODE % COLORS[k])
        self.backgroundemph = SUFFIX_CODE % HIGHLIGHTS['on_red']
        self.onyellowemph = SUFFIX_CODE % HIGHLIGHTS['on_yellow']
        self.oncyanemph = SUFFIX_CODE % HIGHLIGHTS['on_cyan']
        self.reset = RESET

    def buildCode(self, color):
        code = ''
        if color in COLORS:
            code = SUFFIX_CODE % COLORS[color]
        if color in HIGHLIGHTS:
            code += SUFFIX_CODE % HIGHLIGHTS[color]
        return code

    def getCode(self, color):
        '''Returns the color code
        provided the ascii color word'''
        color = [ k.strip() for k in color.split(',') ]
        return ''.join(map(self.buildCode, color))

