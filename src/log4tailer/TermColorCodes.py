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


COLOR_WHITE = 'white'
COLOR_CYAN = 'cyan'
COLOR_MAGENTA = 'magenta'
COLOR_BLUE = 'blue'
COLOR_YELLOW = 'yellow'
COLOR_GREEN = 'green'
COLOR_RED = 'red'
COLOR_BLACK = 'black'
SUFFIX_CODE = '\033[%dm'
RESET = '\033[0m'
SKIP = "skip"

AVAILABLE_COLORS = [COLOR_BLACK, COLOR_RED, COLOR_GREEN, COLOR_YELLOW, COLOR_BLUE, COLOR_MAGENTA, COLOR_CYAN,
                    COLOR_WHITE]
AVAILABLE_BG_COLORS = ['on_' + c for c in AVAILABLE_COLORS]

COLORS = dict(zip(AVAILABLE_COLORS, [SUFFIX_CODE % r for r in range(30, 38)]))

HIGHLIGHTS = dict(
    zip(AVAILABLE_BG_COLORS,
        [SUFFIX_CODE % r for r in range(40, 48)]
    )
)

class TermColorCodes:
    '''Defines the ANSI Terminal
    color codes'''

    def __init__(self):
        self.backgroundemph = HIGHLIGHTS['on_red']
        self.onyellowemph = HIGHLIGHTS['on_yellow']
        self.oncyanemph = HIGHLIGHTS['on_cyan']
        self.reset = RESET

    def buildCode(self, color):
        code = ''
        if color in COLORS:
            code = COLORS[color]
        if color in HIGHLIGHTS:
            code += HIGHLIGHTS[color]
        return code

    def getCode(self, color):
        '''Returns the color code
        provided the ascii color word'''
        if color == SKIP:
            return SKIP
        color = [k.strip() for k in color.split(',')]
        return ''.join(map(self.buildCode, color))

