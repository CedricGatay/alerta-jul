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
import sys
import mocker
import time
import os
from log4tailer import notifications
from log4tailer.Properties import Property
from log4tailer.Message import Message
from log4tailer.LogColors import LogColors
from log4tailer.Log import Log

CONFIG = 'aconfig.txt'
SYSOUT = sys.stdout


# so we can run the tests in ../test or inside test 
# folder
current_directory = os.path.basename(os.getcwd())
EXECUTABLE = 'python executable.py'
if current_directory != 'tests':
    EXECUTABLE = 'python '+ os.path.join('tests', 'executable.py')

class Writer:
    def __init__(self):
        self.captured = []
    
    def __len__(self):
        return len(self.captured)

    def write(self, txt):
        self.captured.append(txt)

class TestExecutor(unittest.TestCase):
    def setUp(self):
        self.mocker = mocker.Mocker()
        sys.stdout = Writer()
    
    def testShouldReadExecutorFromConfigFile(self):
        fh = open(CONFIG, 'w')
        fh.write('executor = ls -l\n')
        fh.close()
        properties = Property(CONFIG)
        properties.parse_properties()
        executor = notifications.Executor(properties)
        self.assertEquals(['ls', '-l'], executor.executable)
        executor.stop()

    def testShouldRaiseIfExecutorNotProvided(self):
        fh = open(CONFIG, 'w')
        fh.write('anything = ls -l\n')
        fh.close()
        properties = Property(CONFIG)
        properties.parse_properties()
        self.assertRaises(Exception, notifications.Executor, properties)

    def testShouldProvideNotifyMethod(self):
        fh = open(CONFIG, 'w')
        fh.write('executor = ls -l\n')
        fh.close()
        properties = Property(CONFIG)
        properties.parse_properties()
        executor = notifications.Executor(properties)
        self.assertTrue(hasattr(executor, 'notify'))

    def testFullTriggerTrueTwoPlaceHoldersBasedOnConfig(self):
        fh = open(CONFIG, 'w')
        fh.write('executor = ls -l %s %s\n')
        fh.close()
        properties = Property(CONFIG)
        properties.parse_properties()
        executor = notifications.Executor(properties)
        self.assertEqual(True, executor.full_trigger_active)
        executor.stop()

    def testFullTriggerFalseBasedOnConfig(self):
        fh = open(CONFIG, 'w')
        fh.write('executor = ls -l\n')
        fh.close()
        properties = Property(CONFIG)
        properties.parse_properties()
        executor = notifications.Executor(properties)
        self.assertEqual(False, executor.full_trigger_active)
        executor.stop()

    def testShouldNotifyWithFullTrigger(self):
        logcolor = LogColors()
        message = Message(logcolor)
        log = Log('anylog')
        fh = open(CONFIG, 'w')
        fh.write('executor = ls -l %s %s\n')
        fh.close()
        trace = "this is a FATAL log trace"
        trigger = ['ls', '-l', trace, log.path ]
        properties = Property(CONFIG)
        properties.parse_properties()
        os_mock = self.mocker.replace('subprocess')
        os_mock.call(' '.join(trigger), shell = True)
        self.mocker.result(True)
        self.mocker.replay()
        # we just verify the trigger gets 
        # called in the tearDown
        executor = notifications.Executor(properties)
        message.parse(trace, log)
        executor.notify(message, log)
        time.sleep(0.0002)
        executor.stop()
    
    def testShouldNotifyWithNoFullTrigger(self):
        logcolor = LogColors()
        message = Message(logcolor)
        log = Log('anylog')
        logpath = log.path
        fh = open(CONFIG, 'w')
        fh.write('executor = echo\n')
        fh.close()
        trace = "this is a fatal log trace"
        properties = Property(CONFIG)
        properties.parse_properties()
        executor = notifications.Executor(properties)
        message.parse(trace, log)
        trigger = executor._build_trigger(trace, logpath)
        self.assertEqual(['echo'], trigger)
        executor.notify(message, log)
        executor.stop()

    def testShouldContinueIfExecutorFails(self):
        logcolor = LogColors()
        message = Message(logcolor)
        log = Log('anylog')
        fh = open(CONFIG, 'w')
        fh.write('executor = anycommand\n')
        fh.close()
        trace = "this is a critical log trace"
        properties = Property(CONFIG)
        properties.parse_properties()
        executor = notifications.Executor(properties)
        message.parse(trace, log)
        executor.notify(message, log)
        time.sleep(0.0002)
        executor.stop()

    def testShouldContinueTailingIfExecutableTakesLongTime(self):
        logcolor = LogColors()
        message = Message(logcolor)
        log = Log('anylog')
        fh = open(CONFIG, 'w')
        fh.write('executor = ' + EXECUTABLE +'\n')
        fh.close()
        trace = "this is an error log trace"
        properties = Property(CONFIG)
        properties.parse_properties()
        executor = notifications.Executor(properties)
        message.parse(trace, log)
        start = time.time()
        executor.notify(message, log)
        finished = time.time()
        ellapsed = start - finished
        time.sleep(0.0002)
        executor.stop()
        # executable.py sleeps for three seconds
        self.assertTrue(ellapsed < 0.1)

    def testShouldNotExecuteIfLevelNotInPullers(self):
        logcolor = LogColors()
        message = Message(logcolor)
        log = Log('anylog')
        fh = open(CONFIG, 'w')
        fh.write('executor = anything %s %s\n')
        fh.close()
        trace = "this is an info log trace"
        properties = Property(CONFIG)
        properties.parse_properties()
        executor = notifications.Executor(properties)
        message.parse(trace, log)
        executor.notify(message, log)
        time.sleep(0.0002)
        executor.stop()
        self.assertFalse(sys.stdout.captured)

    def testShouldExecuteIfTargetMessage(self):
        logcolor = LogColors()
        logfile = 'anylog'
        log = Log(logfile)
        fh = open(CONFIG, 'w')
        fh.write("executor = echo ' %s %s '\n")
        fh.close()
        trace = "this is an info log trace"
        trigger = ['echo', trace, logfile]
        properties = Property(CONFIG)
        properties.parse_properties()
        message = Message(logcolor, target = 'trace')
        executor_mock = self.mocker.mock()
        executor_mock._build_trigger(trace, logfile)
        self.mocker.result(trigger)
        executor_mock.started
        self.mocker.result(True)
        landing_mock = self.mocker.mock()
        landing_mock.landing(trigger)
        self.mocker.result(True)
        executor_mock.trigger_executor
        self.mocker.result(landing_mock)
        self.mocker.replay()
        message.parse(trace, log)
        self.assertTrue(message.isATarget())
        notifications.Executor.notify.im_func(executor_mock, message, log)

    def tearDown(self):
        self.mocker.restore()
        self.mocker.verify()
        sys.stdout = SYSOUT

if __name__ == '__main__':
    unittest.main()

