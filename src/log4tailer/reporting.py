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

from time import time
from log4tailer import utils
from log4tailer import TermColorCodes, Timer
import datetime

MAIL = 'mail'
PRINT = 'print'
FILE = 'file'

def colorize(line, colors):
    return colors.backgroundemph + line + colors.reset

class Resume(object):
    '''Will report of number of debug, info and warn 
    events. For Error and Fatal will provide the timestamp 
    if there was any event of that level'''
    DEFAULT_METHODS = [MAIL, PRINT]

    def __init__(self, arrayLog):
        self.arrayLog = arrayLog
        self.initTime = time()
        self.logsReport = {}
        for log in arrayLog:
            self.logsReport[log.path] = {'TARGET':0,
                                                 'DEBUG':0,
                                                 'INFO':0,
                                                 'WARN':0,
                                                 'OTHERS':[],
                                                 'ERROR':[],
                                                 'FATAL':[],
                                                 'CRITICAL':[]}

        self.nonTimeStamped = ['DEBUG', 'INFO', 'WARN', 'TARGET']
        self.orderReport = ['CRITICAL', 'FATAL', 'ERROR', 'WARN', 'INFO',
                'DEBUG', 'TARGET', 'OTHERS']
        self.mailAction = None
        self.notificationType = PRINT
        self.gapTime = 3600
        self.notifiers = []
        self.is_daemonized = False
        self.timer = Timer.Timer(self.gapTime)
        self.timer.startTimer()
        self.report_file = None

    def add_notifier(self, notifier):
        self.notifiers.append(notifier)

    def flushReport(self):
        for _, dictlog in self.logsReport.iteritems():
            for key, _ in dictlog.iteritems():
                if key in ['ERROR', 'FATAL', 'CRITICAL', 'OTHERS']:
                    dictlog[key] = []
                else:
                    dictlog[key] = 0

    def update(self, message, log):
        messageLevel = message.messageLevel
        plainmessage, _ = message.getPlainMessage()
        isTarget = message.isATarget()
        logPath = log.path
        logKey = self.logsReport[logPath]
        # targets have preference over levels
        if isTarget:
            logKey['TARGET'] += 1
            return
        if logKey.has_key(messageLevel):
            if messageLevel in self.nonTimeStamped:
                logKey[messageLevel] += 1
            else:
                res = utils.get_now()
                logKey[messageLevel].append(res +'=>> '+plainmessage)
        for notifier in self.notifiers:
            if notifier.alerted:
                res = utils.get_now()
                logKey['OTHERS'].append(res + '=>> '+ notifier.alerting_msg)
        self.report_now()

    def report_now_print(self, body):
        return

    def report_now_mail(self, body):
        self.mailAction.sendNotificationMail(body)

    def report_now_file(self, body):
        fh = open(self.report_file, 'a')
        fh.write("#" * 80 + '\n')
        fh.write("Report at " + datetime.datetime.now().isoformat(' ') + '\n')
        fh.write(body)
        fh.close()
    
    def report_now(self):
        if self.notificationType == PRINT and not self.is_daemonized:
            return
        if self.timer.inactivityEllapsed() > self.gapTime:
            body = self.reportBody()
            report_method = 'report_now_' + self.notificationType
            getattr(self, report_method)(body)
            self.flushReport()
            self.timer.reset()
           
    def __execTime(self):
        finish = time()
        ellapsed = finish - self.initTime
        return utils.hours_mins_format(ellapsed)

    def notification_type(self, notification_method):
        """If notification_method is not mail or print, it will be the full
        path to the file where we will report.
        
        :param notification_method: notification type being mail, file or 
            print
        """ 
        if notification_method not in self.DEFAULT_METHODS:
            self.notificationType = FILE
            self.report_file = notification_method
        else:
            self.notificationType = notification_method
        self.timer = Timer.Timer(self.gapTime)
        self.timer.startTimer()
    
    def setMailNotification(self, mailAction):
        self.mailAction = mailAction
        self.notificationType = 'mail'
        self.timer = Timer.Timer(self.gapTime)
        self.timer.startTimer()
    
    def setAnalyticsGapNotification(self,gapTime):
        self.gapTime = float(gapTime)
        self.timer = Timer.Timer(self.gapTime)
        self.timer.startTimer()

    def getGapNotificationTime(self):
        return self.gapTime

    def getNotificationType(self):
        return self.notificationType
    
    def report(self):
        colors = TermColorCodes.TermColorCodes()
        print "Analytics: "
        print "Uptime: "
        print self.__execTime()
        for log in self.arrayLog:
            titleLog = colorize("Report for Log " + log.path, 
                    colors)
            print titleLog
            print "Levels Report: "
            logKey = self.logsReport[log.path]  
            for level in self.orderReport:
                print level+":"
                if level in self.nonTimeStamped:
                    print logKey[level]
                else:
                    for timestamp in logKey[level]:
                        print timestamp
    
    def reportBody(self):
        body = "Analytics: \n"
        body += "Uptime: \n"
        body += self.__execTime()+"\n"
        for log in self.arrayLog:
            titleLog = "Report for Log "+log.path
            fancyheader = len(titleLog) * '='
            body += fancyheader+"\n"
            body += titleLog+"\n"
            body += fancyheader+"\n"
            body += "Levels Report: \n"
            logKey = self.logsReport[log.path]  
            for level in self.orderReport:
                body += level+":\n"
                if level in self.nonTimeStamped:
                    body += str(logKey[level])+"\n"
                else:
                    for timestamp in logKey[level]:
                        body += timestamp+"\n"
        return body

