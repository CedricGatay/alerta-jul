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

from log4tailer.ColorParser import ColorParser
from log4tailer import modes
import re

class Message(object):
    '''the message to be actioned
    and showed being by email, stdout,...'''

    def __init__(self, logcolor, target = None, properties = None):
        self.patarget = None
        self.isTarget = None
        self.currentLogPath = None
        if target:
            # user can provide multiple
            # comma separated targets
            target = self.__getMultipleTargets(target)
            self.patarget = re.compile(target)
        self.color = logcolor
        self.plainMessage = None
        self.colorizedMessage = None
        self.colorparser = ColorParser()
        self.messageLevel = ''
        self.oldMessageLevel = ''
        self.oldLevelColor = None
        self.pauseMode = modes.PauseMode()
        self.targetColor = None
        self.logOwnColor = False
        self.oldLogPath = None
        self.log = None
        self.patOwnTarget = None
        self.isOwnTarget = None
        self.isTarget = None
        if properties:
            self.pauseMode.parse_config(properties)
   
    def isATarget(self):
        if self.isTarget or self.isOwnTarget:
            return True
        return False

    def getColorizedMessage(self):
        '''it returns a tuple, first 
        element the pause associated 
        with the level found and second 
        element the colorized message
        This method is mainly used 
        by the PrintAction action'''
        
        pause = 0 
        level = self.messageLevel
        levelcolor = None
        if not self.plainMessage:
            return (0,'')
        #FIXME too much return exits in this method
        # targets have priority over Levels
        if self.isTarget or self.isOwnTarget:
            self.log.emphcolor = self.targetColor or self.color.backgroundemph
            self.log.wasTarget = True
            return (self.pauseMode.getPause('target'), 
                    self.log.emphcolor + self.plainMessage + self.color.reset)
        
        if self.log.wasTarget and not self.messageLevel:
            return (self.pauseMode.getPause('target'), 
                    self.log.emphcolor + self.plainMessage + self.color.reset)
        
        self.log.wasTarget = False
        if self.messageLevel:
            levelcolor = self.color.getLevelColor(level)
            self.oldMessageLevel = self.messageLevel
            self.oldLevelColor = levelcolor
            self.oldLogPath = self.currentLogPath
            pause = self.pauseMode.getPause(level.lower())
        
        elif self.currentLogPath == self.oldLogPath:
            self.messageLevel = self.oldMessageLevel
            levelcolor = self.oldLevelColor

        if self.logOwnColor:
            return (pause, self.color.getLogColor(self.logOwnColor)
                    + self.plainMessage + self.color.reset)
        elif levelcolor:
            return (pause, levelcolor + self.plainMessage + self.color.reset)
        else:
            return (pause, self.plainMessage)
        
    def __getMultipleTargets(self, target):
        target = target.replace(' ','').replace(',','|')
        return target

    def getPlainMessage(self):
        return (self.plainMessage, self.currentLogPath)
    
    def __parseSetOpts(self, line):
        self.isTarget = None
        self.isOwnTarget = None
        self.targetColor = None
        self.messageLevel = ''
        if line:
            self.plainMessage = line.rstrip()
            self.messageLevel = self.colorparser.parse(line)
            # is target?
            if self.patarget:
                self.isTarget = self.patarget.search(self.plainMessage)
            if self.patOwnTarget:
                for target in self.patOwnTarget:
                    self.isOwnTarget = target.search(self.plainMessage)
                    if self.isOwnTarget:
                        # get the color associated with this target
                        self.targetColor = self.log.targetColor(target)
                        if self.targetColor:
                            self.targetColor = self.color.getLogColor(self.
                                    targetColor)
                        else:
                            self.targetColor = self.color.backgroundemph
                        break
            return
        # if we don't have anything in line
        # just set current Message to unknown
        self.plainMessage = None
        self.messageLevel = 'UNKNOWN'

    def parse(self, line, log):
        '''Need to parse the line
        and check in what level we are in'''
        self.logOwnColor = log.ownOutputColor
        self.currentLogPath = log.path
        self.patOwnTarget = None
        self.log = log
        if log.patTarget:
            self.patOwnTarget = log.logTargetColor.keys()
        self.__parseSetOpts(line)                

