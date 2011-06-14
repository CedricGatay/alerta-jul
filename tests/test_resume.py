# Log4Tailer: A multicolored python tailer for log4J logs
# Copyright (C) 2010 Jordi Carrillo Bosch

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


import unittest
import os
import re
import time
import mox
import mocker
from log4tailer import reporting
from log4tailer.Log import Log
from log4tailer.Properties import Property
from log4tailer.Message import Message
from log4tailer.LogColors import LogColors
from log4tailer import notifications

class TestResume(unittest.TestCase):

    def writer(self,fh,logTraces):
        for line in logTraces:
            fh.write(line+'\n')

    def setUp(self):
        fh = open('out.log','w')
        someLogTracesForOutLog = ['fatal> something went wrong',
                              'error> not so wrong',
                              'warn> be careful',
                              'debug> looking behind the scenes',
                              'info> the app is running',
                              'fatal> the app is in really bad state']
        
        someLogTracesForOut2Log = ['fatal> something went wrong',
                              'error> not so wrong',
                              'warn> be careful',
                              'debug> looking behind the scenes',
                              'info> the app is running',
                              'fatal> the app is in really bad state']

        fh2 = open('out2.log','w')
        self.writer(fh,someLogTracesForOutLog)
        self.writer(fh2,someLogTracesForOut2Log)
        fh.close()
        fh2.close()
        self.mocker = mocker.Mocker()

    def readAndUpdateLines(self, log, message, resume):
        fh = log.openLog()
        lines = [ line.rstrip() for line in fh.readlines() ]
        for line in lines:
            message.parse(line, log)
            resume.update(message, log)

    def testReportResumeForTwoDifferentLogs(self):
        log = Log('out.log')
        log2 = Log('out2.log')
        arrayLogs = [log, log2]
        fh = log.openLog()
        logcolors = LogColors()
        message = Message(logcolors)
        resume = reporting.Resume(arrayLogs)
        for anylog in arrayLogs:
            self.readAndUpdateLines(anylog,message,resume)
        outlogReport = resume.logsReport[log.path]
        expectedOutLogErrorReport = 'error> not so wrong'
        gotLogTrace = outlogReport['ERROR'][0].split('=>> ')[1]
        self.assertEquals(expectedOutLogErrorReport,
                gotLogTrace)
    
    def testShouldReportaTarget(self):
        logline = 'this is a target line and should be reported'
        message = self.mocker.mock()
        message.messageLevel
        self.mocker.result('INFO')
        message.getPlainMessage()
        self.mocker.result((logline, 'out.log'))
        message.isATarget()
        self.mocker.result(True)
        self.mocker.replay()
        mylog = Log('out.log')
        arraylogs = [mylog]
        resume = reporting.Resume(arraylogs)
        resume.update(message,mylog)
        outLogReport = resume.logsReport[mylog.path]
        numofTargets = 1
        gotnumTargets = outLogReport['TARGET']
        self.assertEquals(numofTargets, gotnumTargets)

    def testShouldReportaLogOwnTarget(self):
        logfile = "/any/path/outtarget.log"
        configfile = "aconfig.txt"
        logcolors = LogColors()
        fh = open(configfile, 'w')
        fh.write("targets "+logfile+" = should\n")
        fh.close()
        properties = Property(configfile)
        properties.parse_properties()
        mylog = Log(logfile, properties)
        optional_params = (None, True, logfile)
        self.assertEqual(optional_params, (mylog.ownOutputColor,
            mylog.patTarget, mylog.path))
        arraylogs = [mylog]
        resume = reporting.Resume(arraylogs)
        message = Message(logcolors, properties = properties)
        logtrace = "log trace info target should be reported"
        message.parse(logtrace, mylog)
        resume.update(message, mylog)
        outLogReport = resume.logsReport[mylog.path]
        numofTargets = 1
        gotnumTargets = outLogReport['TARGET']
        self.assertEquals(numofTargets, gotnumTargets)
 
    
    def testTargetsAreNonTimeStampedinResume(self):
        arrayLog = [Log('out.log')]
        resume = reporting.Resume(arrayLog)
        self.assertTrue('TARGET' in resume.nonTimeStamped)
        self.assertTrue('TARGET' in resume.orderReport)
    
    def testShouldSetupMailNotificationIfAnalyticsNotificationIsSetup(self):
        fh = open('aconfig','w')
        fh.write('analyticsnotification = mail\n')
        fh.write('analyticsgaptime = 3600\n')
        fh.close()
        properties = Property('aconfig')
        properties.parse_properties()
        self.assertTrue(properties.is_key('analyticsnotification'))
        arrayLog = [Log('out.log')]
        resume = reporting.Resume(arrayLog)
        mailactionmocker = mox.Mox()
        mailaction = mailactionmocker.CreateMock(notifications.Mail)
        if properties.get_value('analyticsnotification') == 'mail':
            resume.setMailNotification(mailaction)
            self.assertEquals('mail',resume.getNotificationType())
            gaptime = properties.get_value('analyticsgaptime')
            if gaptime:
                resume.setAnalyticsGapNotification(gaptime)
                self.assertEquals(3600,int(resume.getGapNotificationTime()))
        os.remove('aconfig')

    def testReportToAFile(self):
        reportfileFullPath = "reportfile.txt"
        fh = open('aconfig','w')
        fh.write('analyticsnotification = '+ reportfileFullPath +'\n')
        fh.write('analyticsgaptime = 0.1\n')
        fh.close()
        properties = Property('aconfig')
        properties.parse_properties()
        self.assertTrue(properties.is_key('analyticsnotification'))
        log = Log('out.log')
        arrayLog = [log]
        resume = reporting.Resume(arrayLog)
        resume.setAnalyticsGapNotification(0.1)
        resume.notification_type(reportfileFullPath)
        fh = open('out.log')
        lines = fh.readlines()
        fh.close()
        logcolors = LogColors()
        msg = Message(logcolors)
        time.sleep(0.1)
        for line in lines:
            msg.parse(line, log)
            resume.update(msg, log)
        fh = open(reportfileFullPath)
        reportlength = len(fh.readlines())
        fh.close()
        os.remove(reportfileFullPath)
        self.assertEquals(22, reportlength)
        os.remove('aconfig')

    def testShouldReportOtherNotifications(self):
        inactivity_mock = self.mocker.mock()
        inactivity_mock.alerting_msg
        self.mocker.count(1, None)
        self.mocker.result('Inactivity action detected')
        inactivity_mock.alerted
        self.mocker.count(1, None)
        self.mocker.result(True)
        def populate_log():
            fh = open('out2.log', 'w')
            someLogTracesForLog = ['something here',
                              'something there',
                              'something somewhere']
            for line in someLogTracesForLog:
                fh.write(line + '\n')
            fh.close()
        populate_log()
        log = Log('out2.log')
        arrayLogs = [log]
        logcolors = LogColors()
        message = Message(logcolors)
        resume = reporting.Resume(arrayLogs)
        resume.add_notifier(inactivity_mock)
        self.mocker.replay()
        for anylog in arrayLogs:
            self.readAndUpdateLines(anylog, message, resume)
        outlogReport = resume.logsReport[log.path]
        expectedOthersReport = 'Inactivity action detected'
        gotLogTrace = outlogReport['OTHERS'][0].split('=>> ')[1]
        self.assertEquals(expectedOthersReport,
                gotLogTrace)

    def test_levellistflush(self):
        log1 = Log('firstone.log')
        log2 = Log('secondone.log')
        logs = [log1, log2]
        resume = reporting.Resume(logs)
        reports = {'TARGET':0,
             'DEBUG':0,
             'INFO':0,
             'WARN':0,
             'OTHERS':[],
             'ERROR':[],
             'FATAL':[],
             'CRITICAL':[]}
        self.assertEquals(resume.logsReport['firstone.log'], reports)
        self.assertEquals(resume.logsReport['secondone.log'], reports)
        reports_firstone = resume.logsReport['firstone.log']
        tobe_flushed_firstone = [ k for k in reports_firstone if
                isinstance(reports_firstone[k], list) ]
        resume.flushReport()
        flushed_firstone = [ k for k in reports_firstone if
                isinstance(reports_firstone[k], list) ]
        self.assertEquals(tobe_flushed_firstone, flushed_firstone)

    def test_flush_report_aftergaptime_daemonized(self):
        log = Log('out.log')
        arrayLogs = [log]
        logcolors = LogColors()
        message = Message(logcolors)
        resume = reporting.Resume(arrayLogs)
        resume.is_daemonized = True
        resume.gapTime = 0.05
        for anylog in arrayLogs:
            self.readAndUpdateLines(anylog, message, resume)
        time.sleep(0.05)
        resume.update(message, log)
        expected = {'TARGET':0,
             'DEBUG':0,
             'INFO':0,
             'WARN':0,
             'OTHERS':[],
             'ERROR':[],
             'FATAL':[],
             'CRITICAL':[]}
        outlogReport = resume.logsReport[log.path]
        self.assertEquals(expected, outlogReport)

    def tearDown(self):
        self.mocker.restore()
        self.mocker.verify()
        if os.path.exists('aconfig'):
            os.remove('aconfig')
        if os.path.exists('aconfig.txt'):
            os.remove('aconfig.txt')
        os.remove('out.log')
        os.remove('out2.log')

if __name__ == '__main__':
    unittest.main()



