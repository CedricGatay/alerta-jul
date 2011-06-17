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


class PauseMode(object):
    '''In PrintAction if an specific
    level is found, it will pause so we will
    not miss a level'''

    def __init__(self):
        self.defaultLevelPauses = {'finest' : 0, 'finer':0, 'fine':0, 'config':0, 'info':0, 'severe':0, 'debug':0,'info':0, 'warn':0, 
                'warning':0, 
                'error':0, 
                'fatal':0, 
                'critical':0,
                'target':0}

    def getPause(self,level):
        if level in self.defaultLevelPauses.keys():
            return self.defaultLevelPauses[level]
        return 0

    def parse_config(self,properties):
        pauseKeys = ['pausedebug','pauseinfo','pausewarn','pauseerror','pausefatal',
                     'pausecritical','pausetarget']
        for pauseKey in pauseKeys:
            try:
                level = pauseKey.split('pause')[1]
                pauseLevel = float(properties.get_value(pauseKey))
                self.defaultLevelPauses[level] = pauseLevel
            except:
                pass

