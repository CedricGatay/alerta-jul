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


import sys
from log4Exceptions import *
import re

class Property(object):
    '''class to read a user provided key=value config 
    file. Comments supported are # or //'''

    def __init__(self, propertyfile):
        self.propertyfile = propertyfile
        self.lines = []
        self.keys = []
        self.dictproperties = {}
        self.colors={}
        self.levels=[]
        self.blankpat = re.compile(r'^(\s+|#.*|\/\/.*)$')
        self.validsep = ["="]
        self.resep = "|".join(self.validsep)
        self.levelsRe = re.compile(r'^level=(.*)$')
        self.colorsRe = re.compile(r'^color\.(.*)=(.*)$')

    def parse_properties(self):
        # is that a huge config file?
        try:
            fd = open(self.propertyfile,'r')
        except:
            print "could not open property file"
            sys.exit()
        # Generator expression, so does not matter if huge or not actually.
        lines = (k.rstrip() for k in fd if not self.blankpat.search(k))
        for i in lines:
            search = self.levelsRe.search(i)
            if search:
               self.levels.append(search.group(1).lower())
               continue
            search = self.colorsRe.search(i)
            if search:
                level = search.group(1).lower()
                if not level in self.levels:
                    self.levels.append(level)
                    print "Level " + level + " was automagically added to recognized level as a color was defined !"

                self.colors[level] = search.group(2).lower()
                continue

            vals = re.split(self.resep,i)
            # we make it case insensitive.
            key = vals[0].strip().lower()
            value = vals[1].strip()
            if self.dictproperties.has_key(key):
                raise KeyAlreadyExistsException(key+" is duplicated")
            else:
                self.dictproperties[key] = value
        fd.close()
        self.keys = self.dictproperties.keys()

    def get_value(self, key):
        if key in self.dictproperties:
            return self.dictproperties[key]
        return None
    
    def get_keys(self):
        return self.keys

    def get_levels(self):
        return self.levels

    def get_color(self, level):
        if level in self.colors.keys():
           return self.colors[level]
        return None

    def get_color_items(self):
        return self.colors.items()

    def is_key(self,key):
        if key in self.dictproperties:
            return True
        else:
            return False

