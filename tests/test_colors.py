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
import os, sys
from log4tailer.Log import Log
from log4tailer.Message import Message
from log4tailer.LogColors import LogColors
from log4tailer import notifications
from log4tailer.TermColorCodes import TermColorCodes

SYSOUT = sys.stdout

class Writer:
    def __init__(self):
        self.captured = []
    
    def __len__(self):
        return len(self.captured)

    def write(self, txt):
        self.captured.append(txt)

class PropertiesMock(object):
    """docstring for Properties"""
    def __init__(self):
        pass

    def get_keys(self):
        return ['one', 'two']

    def get_value(self, key):
        if key == 'one':
            return 'john'
        else:
            return 'joe'

class PropertiesBackGround(PropertiesMock):
    """docstring for PropertiesBackGround"""
    def get_keys(self):
        return ['fatal']

    def get_value(self, key):
        return "yellow, on_cyan"
        

class TestColors(unittest.TestCase):
    def setUp(self):
        self.logfile = 'out.log'
        fh = open(self.logfile,'w')
        # levels in upper case
        # should be very weird an app
        # logging levels in lowercase

        self.someLogTraces = ['FATAL> something went wrong',
                              'ERROR> not so wrong',
                              'WARN> be careful',
                              'DEBUG> looking behind the scenes',
                              'INFO> the app is running']
        for line in self.someLogTraces:
            fh.write(line+'\n')
        fh.close()

    def testMessage(self):
        logcolors = LogColors() #using default colors
        termcolors = TermColorCodes()
        target = None
        notifier = notifications.Print()
        message = Message(logcolors,target)
        log = Log(self.logfile)
        log.openLog()
        sys.stdout = Writer()
        #testing Colors with default pauseModes
        for count in range(len(self.someLogTraces)):
            line = log.readLine()
            line = line.rstrip()
            level = line.split('>')
            message.parse(line, log)
            output = logcolors.getLevelColor(level[0])+line+termcolors.reset
            notifier.notify(message,log)
            self.assertTrue(output in sys.stdout.captured)
        
        line = log.readLine()
        self.assertEqual('',line)
        message.parse(line, log)
        self.assertFalse(notifier.notify(message,log))
    
    def testshouldColorizefirstLevelFoundignoringSecondinSameTrace(self):
        # Test for fix 5
        # Should give priority to FATAL in next trace
        level = 'FATAL'
        trace = "FATAL there could be an error in the application"
        sys.stdout = Writer()
        logcolors = LogColors()
        termcolors = TermColorCodes()
        message = Message(logcolors)
        notifier = notifications.Print()
        anylog = Log('out.log')
        message.parse(trace, anylog)
        output = logcolors.getLevelColor(level)+trace+termcolors.reset
        notifier.notify(message,anylog)
        self.assertEqual(output, sys.stdout.captured[0])

    def testshouldNotColorizeifLevelKeyInaWord(self):
        # Testing boundary regex as for suggestion of 
        # Carlo Bertoldi
        trace = "this is a logtrace where someinfoword could be found"
        sys.stdout = Writer()
        logcolors = LogColors()
        message = Message(logcolors)
        notifier = notifications.Print()
        anylog = Log('out.log')
        message.parse(trace, anylog)
        notifier.notify(message,anylog)
        self.assertEqual(trace, sys.stdout.captured[0])
        self.assertEqual('', message.messageLevel)        
    
    def testLogColorsParseConfig(self):
        logcolors = LogColors()
        logcolors.parse_config(PropertiesMock())
        self.assertFalse(hasattr(logcolors,'one'))
        self.assertFalse(hasattr(logcolors,'two'))

    def testshouldColorizeMultilineLogTraces(self):
        trace = 'FATAL> something went wrong\nin here as well'
        trace0, trace1 = trace.split('\n')
        level = 'FATAL'
        termcolors = TermColorCodes()
        # now assert trace0 and trace1 are in FATAL level
        sys.stdout = Writer()
        logcolors = LogColors()
        message = Message(logcolors)
        notifier = notifications.Print()
        anylog = Log('out.log')
        expectedLogTrace0 = logcolors.getLevelColor(level) + \
                trace0 + termcolors.reset
        expectedLogTrace1 = logcolors.getLevelColor(level) + \
                trace1 + termcolors.reset
        message.parse(trace0, anylog)
        notifier.notify(message, anylog)
        self.assertEqual(expectedLogTrace0, sys.stdout.captured[0])
        self.assertEqual('FATAL', message.messageLevel)        
        message.parse(trace1, anylog)
        notifier.notify(message, anylog)
        self.assertEqual(expectedLogTrace1, sys.stdout.captured[2])
        self.assertEqual('FATAL', message.messageLevel)        

    def testshouldColorizeWithBackground(self):
        trace = "FATAL there could be an error in the application"
        level = 'FATAL'
        sys.stdout = Writer()
        logcolors = LogColors()
        logcolors.parse_config(PropertiesBackGround())
        termcolors = TermColorCodes()
        message = Message(logcolors)
        notifier = notifications.Print()
        anylog = Log('out.log')
        message.parse(trace, anylog)
        output = logcolors.getLevelColor(level)+trace+termcolors.reset
        notifier.notify(message,anylog)
        self.assertEqual(output, sys.stdout.captured[0])
    
    def testshouldFailColorizeWithBackground(self):
        trace = "FATAL there could be an error in the application"
        level = 'WARN'
        sys.stdout = Writer()
        logcolors = LogColors()
        termcolors = TermColorCodes()
        logcolors.parse_config(PropertiesBackGround())
        message = Message(logcolors)
        notifier = notifications.Print()
        anylog = Log('out.log')
        message.parse(trace, anylog)
        output = logcolors.getLevelColor(level)+trace+termcolors.reset
        notifier.notify(message,anylog)
        self.assertNotEqual(output, sys.stdout.captured[0])

    def testShouldColorizeWarningLevelAsWell(self):
        '''test that *warning* keyword gets colorized as well'''
        level = 'WARNING'
        trace = "WARNING there could be an error in the application"
        sys.stdout = Writer()
        logcolors = LogColors()
        termcolors = TermColorCodes()
        message = Message(logcolors)
        notifier = notifications.Print()
        anylog = Log('out.log')
        message.parse(trace, anylog)
        output = logcolors.getLevelColor(level)+trace+termcolors.reset
        notifier.notify(message,anylog)
        self.assertEqual(output, sys.stdout.captured[0])

    def tearDown(self):
        sys.stdout = SYSOUT
        os.remove(self.logfile)

if __name__ == '__main__':
    unittest.main()



