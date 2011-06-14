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
from log4tailer.Properties import Property
from log4tailer.log4Exceptions import KeyAlreadyExistsException

class TestProperties(unittest.TestCase):
    
    def setUp(self):
        self.configfile = 'config.txt'
        self.configfh = open(self.configfile,'w')
        colorconfigs = {'warn':'yellow','fatal':'red',
                        'error':'red'}
        for key,value in colorconfigs.iteritems():
            self.configfh.write(key +'='+value+'\n')

        self.configfh.close()
        self.configKeys = colorconfigs.keys().sort()

    def testparse_properties(self):
        property = Property(self.configfile)
        property.parse_properties()
        configPropertyKeys = property.get_keys().sort()
        # my colorconfigs keys are already in lowercase
        self.assertEqual(self.configKeys,configPropertyKeys)
    
    def testcontainsOwnTargetLog(self):
        self.configfh = open('anotherconfig.txt','w')
        key = "targets /var/log/messages" 
        value = "$2009-08-09 anything, ^regex2"
        targetline = key+"="+value+"\n"
        self.configfh.write(targetline)
        self.configfh.close()
        property = Property('anotherconfig.txt')
        property.parse_properties()
        self.assertEqual(value,property.get_value(key))
        os.remove('anotherconfig.txt')

    def testshouldReturnNoneifKeyNotFound(self):
        property = Property(self.configfile)
        property.parse_properties()
        key = 'hi'
        self.assertFalse(property.get_value(key))
    
    def __createDuplicateKeysConfig(self):
        os.remove(self.configfile)
        configfh = open(self.configfile,'w')
        colorconfigs = {'warn':'yellow','fatal':'red','error':'red'}
        for key,value in colorconfigs.iteritems():
            configfh.write(key +'='+value+'\n')
        # making a duplicate level
        configfh.write('warn'+'='+'red'+'\n')
        configfh.close()

    def testKeyAlreadyExistsException(self):                                    
        self.__createDuplicateKeysConfig()
        property = Property(self.configfile)
        self.assertRaises(KeyAlreadyExistsException,property.parse_properties)

    def tearDown(self):
        os.remove(self.configfile)



if __name__=='__main__':
    unittest.main()





