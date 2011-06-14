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

# Thanks to Carlo Bertoldi for suggesting a better regex.

import re

EQUIVALENT_LEVELS = {'WARNING' : 'WARN'}

class ColorParser(object):
    '''tries to parse 
    defined levels in log4j'''

    def __init__(self):
        self.all = re.compile(r'.*?\b(debug|info|warn|warning|error|fatal|critical)\b', 
                re.I)

    def parse(self, line):
        isMatch = self.all.match(line)
        if isMatch:
            level = isMatch.group(1).upper()
            return EQUIVALENT_LEVELS.get(level, level)
        return ''
       
