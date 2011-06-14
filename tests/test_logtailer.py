import unittest
import sys
import mocker
import time
import os
import signal
import re
import threading
from mocker import ANY
import copy
from log4tailer import reporting
from log4tailer.LogTailer import LogTailer
from log4tailer.LogColors import LogColors
from log4tailer import notifications
from log4tailer.Log import Log
from log4tailer.Properties import Property
import log4tailer
from tests import LOG4TAILER_DEFAULTS

SYSOUT = sys.stdout

class Writer:
    def __init__(self):
        self.captured = []

    def __len__(self):
        return len(self.captured)

    def write(self, txt):
        self.captured.append(txt)


def getDefaults():
    return {'pause' : 0, 
        'silence' : False,
        'throttle' : 0,
        'actions' : [notifications.Print()],
        'nlines' : False,
        'target': None, 
        'logcolors' : LogColors(),
        'properties' : None,
        'alt_config': None}

class TestResume(unittest.TestCase):

    def setUp(self):
        self.mocker = mocker.Mocker()
    
    def testshouldReturnTrueifMailAlreadyinMailAction(self):
        mailaction_mock = self.mocker.mock(notifications.Mail)
        self.mocker.replay()
        defaults = getDefaults()
        defaults['actions'] = [mailaction_mock]
        logtailer = LogTailer(defaults)
        self.assertEqual(True,logtailer.mailIsSetup())

    def __setupAConfig(self, method = 'mail'):
        fh = open('aconfig','w')
        fh.write('inactivitynotification = ' + method + '\n')
        fh.close()

    def testshouldReturnFalseMailNotSetup(self):
        self.__setupAConfig()
        properties = Property('aconfig')
        properties.parse_properties()
        defaults = getDefaults()
        defaults['properties'] = properties
        logtailer = LogTailer(defaults)
        self.assertEqual(False,logtailer.mailIsSetup())
    
    def testReturnsFalseifMailActionOrInactivityActionNotificationNotEnabled(self):
        logtailer = LogTailer(getDefaults())
        self.assertEqual(False,logtailer.mailIsSetup())
    
    def testPipeOutShouldSendMessageParseThreeParams(self):
        sys.stdin = ['error > one error', 'warning > one warning']
        sys.stdout = Writer()
        logtailer = LogTailer(getDefaults())
        logtailer.pipeOut()
        self.assertTrue('error > one error' in sys.stdout.captured[0])

    def testResumeBuilderWithAnalyticsFile(self):
        sys.stdout = Writer()
        reportfile = 'reportfile.txt'
        configfile = 'aconfig'
        fh = open(configfile, 'w')
        fh.write('analyticsnotification = ' + reportfile + '\n')
        fh.close()
        properties = Property(configfile)
        properties.parse_properties()
        defaults = getDefaults()
        defaults['properties'] = properties
        logtailer = LogTailer(defaults)
        resumeObj = logtailer.resumeBuilder()
        self.assertTrue(isinstance(resumeObj, reporting.Resume))
        self.assertEquals('file', resumeObj.getNotificationType())
        self.assertEquals(reportfile, resumeObj.report_file)

    def testResumeBuilderWithInactivityAction(self):
        defaults = getDefaults()
        defaults['actions'] = [notifications.Inactivity(5)]
        tailer = LogTailer(defaults)
        resume = tailer.resumeBuilder()
        self.assertTrue(isinstance(resume.notifiers[0],
            notifications.Inactivity)) 

    def tearDown(self):
        self.mocker.restore()
        self.mocker.verify()
        sys.stdout = SYSOUT


class Interruptor(threading.Thread):
    log_name = 'out.log'
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.pid = os.getpid()

    def run(self):
        onelogtrace = 'this is an info log trace'
        anotherlogtrace = 'this is a debug log trace'
        fh = open(self.log_name, 'a')
        fh.write(onelogtrace + '\n')
        fh.write(anotherlogtrace + '\n')
        fh.close()
        time.sleep(0.02)
        os.kill(self.pid, signal.SIGINT)

class TestTailer(unittest.TestCase):
    log_name = 'out.log'
   
    def setUp(self):
        self.onelog = Log(self.log_name)
        onelogtrace = 'this is an info log trace'
        anotherlogtrace = 'this is a debug log trace'
        fh = open(self.log_name, 'w')
        fh.write(onelogtrace + '\n')
        fh.write(anotherlogtrace + '\n')
        fh.close()
    
    def test_tailerPrintAction(self):
        sys.stdout = Writer()
        tailer = LogTailer(getDefaults())
        tailer.addLog(self.onelog)
        interruptor = Interruptor()
        interruptor.start()
        tailer.tailer()
        interruptor.join()
        finish_trace = re.compile(r'because colors are fun')
        found = False
        for num, line in enumerate(sys.stdout.captured):
            if finish_trace.search(line):
                found = True
        if not found:
            self.fail()

    def tearDown(self):
        sys.stdout = SYSOUT
        if os.path.exists(self.log_name):
            os.remove(self.log_name)

class TestInit(unittest.TestCase):
    def setUp(self):
        self.mocker = mocker.Mocker()

    def __options_mocker_generator(self, mock, params):
        for key, val in params.iteritems():
            getattr(mock, key)
            self.mocker.result(val)
    
    class OptionsMock(object):
        def __init__(self):
            pass
        def __getattr__(self, name):
            if name == 'inactivity':
                return True
            elif name == 'configfile':
                return "anythingyouwant"
            return False

    def test_monitor_inactivity_nomail(self):
        options_mock = self.mocker.mock()
        options_mock.inactivity
        self.mocker.result(True)
        self.mocker.count(1,2)
        params = {'configfile' : 'anythingyouwant', 
                'version' : False,
                'filter' : False,
                'tailnlines' : False,
                'target' : False,
                'cornermark' : False,
                'executable' : False,
                'post' : False,
                'pause' : False,
                'throttle' : False,
                'silence' : False, 
                'mail' : False,
                'nomailsilence' : False,
                'screenshot' : False}
        self.__options_mocker_generator(options_mock, params)
        self.mocker.replay()
        log4tailer.initialize(options_mock)
        actions = log4tailer.defaults['actions']
        self.assertEquals(2, len(actions))
        self.assertTrue(isinstance(actions[0], notifications.Print))
        self.assertTrue(isinstance(actions[1], notifications.Inactivity))
        self.assertFalse(isinstance(actions[0], notifications.CornerMark))

    def test_monitor_inactivity_withmail(self):
        properties_mock = self.mocker.mock()
        properties_mock.get_value('inactivitynotification')
        self.mocker.result('mail')
        properties_mock.get_keys()
        self.mocker.result([])
        defaults = getDefaults()
        defaults['properties'] = properties_mock
        log4tailer.defaults = defaults
        utils_mock = self.mocker.replace('log4tailer.utils.setup_mail')
        utils_mock(ANY)
        self.mocker.result(True)
        self.mocker.replay()
        log4tailer.initialize(self.OptionsMock())
        actions = log4tailer.defaults['actions']
        self.assertEquals(2, len(actions))
        self.assertTrue(isinstance(actions[0], notifications.Print))
        self.assertTrue(isinstance(actions[1], notifications.Inactivity))
        self.assertFalse(isinstance(actions[0], notifications.CornerMark))

    def test_corner_mark_setup(self):
        options_mock = self.mocker.mock()
        options_mock.cornermark
        self.mocker.count(1, 2)
        self.mocker.result(True)
        params = {'configfile' : 'anythingyouwant', 
                'version' : False,
                'filter' : False,
                'tailnlines' : False,
                'target' : False,
                'executable' : False,
                'pause' : False,
                'throttle' : False,
                'silence' : False, 
                'mail' : False,
                'inactivity' : False,
                'nomailsilence' : False,
                'post' : False,
                'screenshot' : False}
        self.__options_mocker_generator(options_mock, params)
        self.mocker.replay()
        log4tailer.initialize(options_mock)
        actions = log4tailer.defaults['actions']
        self.assertEquals(2, len(actions))
        self.assertTrue(isinstance(actions[0], notifications.Print))
        self.assertTrue(isinstance(actions[1], notifications.CornerMark))

    def test_daemonized_resumedaemonizedtrue(self):
        defaults = getDefaults()
        defaults['silence'] = True
        logtailer = LogTailer(defaults)
        resumeObj = logtailer.resumeBuilder()
        self.assertTrue(isinstance(resumeObj, reporting.Resume))
        self.assertEquals('print', resumeObj.getNotificationType())
        self.assertTrue(resumeObj.is_daemonized)

    def tearDown(self):
        self.mocker.restore()
        self.mocker.verify()
        log4tailer.defaults = copy.deepcopy(LOG4TAILER_DEFAULTS)

if __name__ == '__main__':
    unittest.main()


