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

import os
import time
import sys
from log4tailer.Message import Message
from log4tailer.Log import Log
from log4tailer.reporting import Resume
from log4tailer import notifications
from log4tailer.utils import setup_mail, daemonize


def get_term_lines():
    termlines = os.popen("tput lines")
    ttlines = termlines.readline()
    termlines.close()
    ttlines = int(ttlines)
    return ttlines

def _printHeaderLog(path):
    print "==> "+path+" <=="

def hasRotated(log):
    """Returns True if log has rotated
    False otherwise"""
    if log.getcurrInode()!=log.inode or log.getcurrSize() < log.size: 
        print "Log "+log.path+" has rotated"
        # close the log and open it again 
        log.closeLog()
        log.openLog()
        log.seekLogEnd()
        return True
    return False

class LogTailer(object):
    '''Tails the logs provided by Log class'''
    def __init__(self, defaults):
        self.arrayLog = []
        self.logcolors = defaults['logcolors']
        self.pause = defaults['pause']
        self.silence = defaults['silence']
        self.actions = defaults['actions']
        self.throttleTime = defaults['throttle']
        self.target = defaults['target']
        self.properties = defaults['properties']
        self.mailAction = None

    def addLog(self, log):
        self.arrayLog.append(log)

    def posEnd(self):
        '''Open the logs and position the cursor
        to the end'''
        for log in self.arrayLog:
            log.openLog()
            log.seekLogNearlyEnd()

    def __initialize(self, message):
        '''prints the last 10 
        lines for each log, one log 
        at a time''' 
        printAction = notifications.Print()
        lenarray = len(self.arrayLog)
        cont = 0
        for log in self.arrayLog:
            cont += 1
            _printHeaderLog(log.path)
            line = log.readLine()
            while line != '':
                line = line.rstrip()
                message.parse(line, log)
                printAction.printInit(message)
                line = log.readLine()
            # just to emulate the same behaviour as tail
            if cont < lenarray:
                print

    def printLastNLines(self,n):
        '''tail -n numberoflines method in pager mode'''
        message = Message(self.logcolors)
        action = notifications.Print()
        for log in self.arrayLog:
            fd = log.openLog()
            numlines = log.numLines()
            pos = numlines-n
            count = 0
            buff = []
            ttlines = get_term_lines()
            for curpos,line in enumerate(fd):
                if curpos >= pos:
                    line = line.rstrip()
                    message.parse(line, log)
                    action.notify(message, log)
                    count += 1
                    buff.append(line)
                    if (count % ttlines) == 0:
                        raw_input("continue\n")
                        count = 0
                        ttlines = get_term_lines()
            log.closeLog()
    
    def pipeOut(self):
        """Reads from standard input 
        and prints to standard output"""
        message = Message(self.logcolors, self.target, self.properties)
        stdin = sys.stdin
        anylog = Log('anylog')
        for line in stdin:
            message.parse(line, anylog)
            for action in self.actions:
                action.notify(message, anylog)
    
    def __getAction(self,module):
        for action in self.actions:
            if isinstance(action, module):
                return action
        return None

    def mailIsSetup(self):
        '''check if mail properties
        already been setup'''
        properties = self.properties
        action = self.__getAction(notifications.Mail)
        if action:
            self.mailAction = action
            return True
        if properties:
            if properties.get_value('inactivitynotification') == 'mail':
                # check if there is any inactivity action actually setup
                inactivityaction = self.__getAction(notifications.Inactivity)
                if inactivityaction:
                    self.mailAction = inactivityaction.getMailAction()
                    return True
        return False
    
    def resumeBuilder(self):
        resume = Resume(self.arrayLog)
        notify_defaults = ('mail', 'print')
        properties = self.properties
        if properties:
            notification_type = properties.get_value('analyticsnotification')
            analyticsgap = properties.get_value('analyticsgaptime')
            if notification_type and notification_type not in notify_defaults:
                resume.notification_type(notification_type)
            elif notification_type == 'mail':
                if not self.mailIsSetup():
                    mailAction = setup_mail(properties)
                    resume.setMailNotification(mailAction)
                else:
                    resume.setMailNotification(self.mailAction)
            if analyticsgap:
                resume.setAnalyticsGapNotification(analyticsgap)
        if self.silence:
            # if no notify has been setup and we are in daemonized mode 
            # we need to flush the reporting to avoid filling up memory.
            resume.is_daemonized = True
        # check if inactivity action on the self.actions and set the inactivity 
        # on the resume object. If inactivity is flagged, will be then
        # reported.
        inactivity_action = self.__getAction(notifications.Inactivity)
        if inactivity_action:
            resume.add_notifier(inactivity_action)
        return resume
    
    def notifyActions(self, message, log):
        for action in self.actions:
            action.notify(message, log)

    def tailer(self):
        '''Stdout multicolor tailer'''
        message = Message(self.logcolors,self.target,self.properties)
        resume = self.resumeBuilder()
        self.posEnd()
        get_log_lines = "readLines"
        if self.throttleTime:
            get_log_lines = "readLine"
        if self.silence:
            daemonize()
        try:
            self.__initialize(message)
            lastLogPathChanged = ""
            curpath = ""
            while True:
                found = 0
                time.sleep(self.throttleTime)
                for log in self.arrayLog:
                    curpath = log.path
                    if hasRotated(log):
                        found = 0
                    lines = getattr(log, get_log_lines)()
                    if not lines:
                        # notify actions
                        message.parse('', log)
                        resume.update(message, log)
                        self.notifyActions(message, log)
                        continue
                    if isinstance(lines, str):
                        lines = [lines]
                    for line in lines:
                        found = 1
                        line = line.rstrip()
                        # to emulate the tail command
                        if curpath != lastLogPathChanged:
                            print
                            _printHeaderLog(log.path)
                        lastLogPathChanged = log.path
                        message.parse(line, log)
                        resume.update(message, log)
                        self.notifyActions(message, log)
                    log.size = log.getcurrSize()
                if found == 0:
                    #sleep for 1 sec
                    time.sleep(self.pause)
        except (KeyboardInterrupt, OSError, IOError):
            for log in self.arrayLog:
                log.closeLog()
            if self.mailAction:
                self.mailAction.quitSMTP()
            for action in self.actions:
                # executor notification
                if hasattr(action, 'stop'):
                    action.stop()
                # post notification
                if hasattr(action, 'unregister'):
                    for log in self.arrayLog:
                        action.unregister(log)
            print "\n"
            resume.report()
            print "Ended log4tailer, because colors are fun"

