import unittest
import os
from log4tailer import modes
from log4tailer.Properties import Property

class TestPauseMode(unittest.TestCase):
    
    def setUp(self):
        self.configfile = 'config.txt'
        self.configfh = open(self.configfile,'w')
        
        self.overridenLevelPauses = {'pausedebug':2, 'pauseinfo':3,
                                     'pausewarn':4, 'pauseerror':5,
                                     'pausefatal':6, 'pausetarget':7}

        for key,value in self.overridenLevelPauses.iteritems():
            self.configfh.write(key +'='+str(value)+'\n')
        self.configfh.close()
    
    def testgetDefaultPauseModeLevels(self):
        pauseMode = modes.PauseMode()
        self.assertEqual(0,pauseMode.getPause('debug'))
        self.assertEqual(0,pauseMode.getPause('info'))
        self.assertEqual(0,pauseMode.getPause('warn'))
        self.assertEqual(0,pauseMode.getPause('error'))
        self.assertEqual(0,pauseMode.getPause('fatal'))
        self.assertEqual(0,pauseMode.getPause('target'))

    def testgetOverridePauseModeLevels(self):
        pauseMode = modes.PauseMode()
        properties = Property(self.configfile)
        properties.parse_properties()
        pauseMode.parse_config(properties)
        for key,value in self.overridenLevelPauses.iteritems():
            key = key.split('pause')[1]
            self.assertEqual(value,pauseMode.getPause(key))
    
    def tearDown(self):
        os.remove(self.configfile)

if __name__=='__main__':
    unittest.main()





