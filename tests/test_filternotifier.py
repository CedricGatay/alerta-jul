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
import re
from log4tailer import notifications
from log4tailer.Message import Message
from log4tailer.LogColors import LogColors
from log4tailer.Log import Log
from log4tailer.TermColorCodes import TermColorCodes

SYSOUT = sys.stdout

class Writer:
    def __init__(self):
        self.captured = []
    
    def __len__(self):
        return len(self.captured)

    def write(self, txt):
        self.captured.append(txt)

class TestFilterNotifier(unittest.TestCase):
    def setUp(self):
        pass
    
    def testimplementsFilter(self):
        filterRegexPat = re.compile(r'this not to be printed')
        filterNotifier = notifications.Filter(filterRegexPat)
        self.assertTrue(isinstance(filterNotifier, notifications.Filter))
        self.assertTrue(hasattr(filterNotifier, 'notify'))

    def testnotify(self):
        pattern = re.compile(r'hi, this line to be notified')
        trace = "info hi, this line to be notified"
        level = "INFO"
        notifier = notifications.Filter(pattern)
        sys.stdout = Writer()
        logcolors = LogColors()
        termcolors = TermColorCodes()
        message = Message(logcolors)
        anylog = Log('out.log')
        message.parse(trace, anylog)
        notifier.notify(message, anylog)
        output = logcolors.getLevelColor(level)+trace+termcolors.reset
        self.assertEqual(output, sys.stdout.captured[0])

    def testnoNotification(self):
        pattern = re.compile(r'hi, this line to be notified')
        trace = "info this is just a log trace"
        notifier = notifications.Filter(pattern)
        sys.stdout = Writer()
        logcolors = LogColors()
        message = Message(logcolors)
        anylog = Log('out.log')
        message.parse(trace, anylog)
        notifier.notify(message, anylog)
        # assert is empty
        self.assertFalse(sys.stdout.captured)

    def tearDown(self):
        sys.stdout = SYSOUT

if __name__ == '__main__':
    unittest.main()

