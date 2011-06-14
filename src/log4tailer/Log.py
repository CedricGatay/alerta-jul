# Log4Tailer: A multicolored python tailer for log4J logs
# Copyright (C) 2008 Jordi Carrillo Bosch

# This file is part of Log4Tailer Project.
#
# Log4Tailer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.  #
# Log4Tailer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Log4Tailer.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
from stat import ST_INO, ST_SIZE
from log4tailer.Timer import Timer

class Log(object):
    '''Class that defines a common
    structure in a log'''
    
    TARGET_PROPERTY_PREFIX = "targets "

    def __init__(self, path, properties=None, options=None):
        self.path = path
        self.fh = None
        self.inode = None
        self.size = None
        self.loglevel = None
        self.properties = properties
        self.ownOutputColor = None
        self.ownTarget = None    
        self.patTarget = None
        self.inactivityTimer = None
        self.inactivityAccTime = 0
        self.mailTimer = Timer(60)
        self.mailTimer.startTimer()
        self.logTargetColor = {}
        self.wasTarget = False
        self.emphcolor = None
        if properties:
            self.ownOutputColor = properties.get_value(path.lower())
            self.ownTarget = properties.get_value(Log.TARGET_PROPERTY_PREFIX + 
                    path.lower())
            if self.ownTarget:
                self.logTargetColor = self.targets_colors()
                self.patTarget = True
        if options and options.inactivity:
            self.inactivityTimer = Timer(float(options.inactivity))
            self.inactivityTimer.startTimer()
        self.triggeredNotSent = False
        
    def getcurrInode(self):
        try:
            inode = os.stat(self.path)[ST_INO]
        except OSError:
            print "Could not stat, file removed?"
            raise OSError
        return inode

    def getcurrSize(self):
        size = os.stat(self.path)[ST_SIZE]
        return size
    
    def openLog(self):
        try:
            self.size = os.stat(self.path)[ST_SIZE]
            self.inode = os.stat(self.path)[ST_INO]
        except OSError:
            print "file "+self.path+" does not exist"
            raise OSError
        try:
            fd = open(self.path,'r')
            self.fh = fd
            return fd
        except IOError:
            print "Could not open file "+self.path
            raise IOError
    
    def readLine(self):
        return self.fh.readline()

    def readLines(self):
        return self.fh.readlines()

    def closeLog(self):
        self.fh.close()

    def seekLogEnd(self):
        # should be 2 for versions 
        # older than 2.5 SEEK_END = 2
        self.fh.seek(0,2)
    
    def seekLogNearlyEnd(self):
        currpos = self.__getLast10Lines()
        self.fh.seek(currpos,0)
    
    def __getLast10Lines(self):
        linesep = '\n'
        self.seekLogEnd()
        charRead = ''
        numLines = 0
        # read one char at a time
        # as we get only last 10 lines
        # is not gonna be a lot of effort
        blockReadSize = 1
        blockCount = 1
        try:
            self.fh.seek(-blockReadSize,2)
        except:
            # file is empty, so return
            # with position beginning of file
            return 0
        while (numLines <= 10):
            charRead = self.fh.read(blockReadSize)
            posactual = self.fh.tell()
            blockCount += 1
            if charRead == linesep:
                numLines += 1
            try:
                self.fh.seek(-blockReadSize*blockCount,2)
            except IOError:
                # already reached beginning 
                # of file
                currpos = self.fh.tell()-posactual
                return currpos
        # add 2, to get rid of the last seek -1 
        # and the following \n
        currpos = self.fh.tell()+2
        return currpos

    def numLines(self):
        count = -1
        for count, _ in enumerate(open(self.path,'rU')):
            pass
        count += 1
        return count

    def setInactivityAccTime(self, acctime):
        if acctime == 0:
            self.inactivityAccTime = 0
            return
        self.inactivityAccTime += acctime

    def targetColor(self, target):
        return self.logTargetColor.get(target, '')

    def targets_colors(self):
        """{ compiled regex : color) }
        """ 
        targetcolor = {}
        fields = [ k.strip() for k in self.ownTarget.split(';') ]
        for field in fields:
            regcolor = [ k.strip() for k in field.split(':') ]
            regex = re.compile(regcolor[0])
            if len(regcolor) == 2:
                targetcolor[regex] = regcolor[1]
            else:
                targetcolor[regex] =  None
        return targetcolor

