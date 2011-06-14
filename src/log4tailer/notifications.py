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

import sys
import os
import time
from log4tailer import LogColors
from log4tailer.Timer import Timer
from smtplib import SMTP, SMTPServerDisconnected
from log4tailer.TermColorCodes import TermColorCodes
import subprocess
from subprocess import PIPE
import threading
import httplib

try:
    import json
except:
    try:
        import simplejson as json
    except:
        print ("no json library could be imported, "
                "you need simplejson for Poster notification")

try:
    import queue
except ImportError:
    import Queue as queue

try:
    import SMTP_SSL
except ImportError:
    pass

class Print(object):
    '''PrintAction: prints to stdout the 
    colorized log traces'''

    def __init__(self):
        pass
    
    def notify(self, message, log):
        '''msg should be colorized already
        there is a module in pypy colorize, check it out'''
        (pause, colormsg) = message.getColorizedMessage()
        if colormsg:
            print colormsg
            time.sleep(pause)

    def printInit(self, message):
        (pause,colormsg) = message.getColorizedMessage()
        pause = 0
        if colormsg:
            print colormsg

class PrintShot(Print):
    """Prints log trace and takes 
    an screenshot whenever we find an alertable 
    log trace.""" 

    Pullers = ['ERROR', 'FATAL', 'CRITICAL']
    
    def __init__(self, properties):
        self.screenshot = properties.get_value('screenshot')
        self.winid = self.get_windowsid()
        self.screenproc = ['import', '-window', self.winid, 
                self.screenshot]

    def notify(self, message, log):
        Print.notify(self, message, log)
        msg_level = message.messageLevel.upper()
        if not message.isATarget() and msg_level not in self.Pullers:
            return
        try:
            subprocess.call(self.screenproc)
        except Exception, err:
            print err

    def get_windowsid(self):
        getId = "xprop -root | grep '_NET_ACTIVE_WINDOW(WINDOW)'"
        try:
            proc = subprocess.Popen(getId, shell = True, 
                    stdout = PIPE, stderr = PIPE)
        except Exception, err:
            print err
            return
        res, err = proc.communicate()
        if err:
            return 
        winid = (res.split('#'))[1].strip()
        return winid

class Inactivity(object):
    '''sends an email or print
    alert in case too much inactivity
    in the log.
    This action must be triggered everytime 
    we scan in the log.'''

    InactivityActionNotification = 'inactivitynotification'

    def __init__(self, inactivityTime, properties=None):
        self.inactivityTime = inactivityTime
        self.logColors = LogColors.LogColors()
        self.acumulativeTime = 0
        self.mailAction = None
        notification = None
        if properties:
            notification = properties.get_value(
                    Inactivity.InactivityActionNotification)
            self.logColors.parse_config(properties)
        self.notification = notification or 'print'
        self.alerted = False
        self.alerting_msg = 'Inactivity action detected'

    def notify(self, message, log):
        plainmessage, logpath = message.getPlainMessage()
        timer = log.inactivityTimer
        if not plainmessage:
            ellapsedTime = timer.inactivityEllapsed()
            if self.alerted:
                # already alerted
                self.alerted = False
            if ellapsedTime > float(self.inactivityTime):
                self.alerted = True
                log.setInactivityAccTime(ellapsedTime)
                messageAlert = ("Inactivity in the log " + logpath + " for " +
                        str(log.inactivityAccTime) + " seconds")
                if self.notification == 'print':
                    print (self.logColors.backgroundemph+messageAlert+
                            self.logColors.reset)
                elif self.notification == 'mail':
                    self.mailAction.setBodyMailAction(messageAlert)
                    self.mailAction.triggerAction(message,log)
                    self.mailAction.setBodyMailAction(None)
                timer.reset()
        # else if we got sth in message then, means we got 
        # some kind of activity, so do nothing
        else:
            #start the timer again
            timer.reset()
            log.setInactivityAccTime(0)
            ellapsedTime = 0
            self.alerted = False

    def getNotificationType(self):
        return self.notification

    def setMailNotification(self,mailAction):
        '''sets a mailAction for inactivityAction notification'''
        self.notification = 'mail'
        self.mailAction = mailAction

    def getMailAction(self):
        return self.mailAction

class Mail(object):
    """Common actions to be taken
    by the Tailer"""
    
    mailLevels = ['CRITICAL', 'ERROR', 'FATAL']
    weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    monthname = [None,
                 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    def __init__(self, fro = None, to = None, hostname = None, user = None,
            passwd = None, port = 25, ssl = "False"):
        self.fro = fro
        self.to = to
        self.hostname = hostname
        self.user = user
        self.passwd = passwd
        self.conn = None
        self.bodyMailAction = None
        self.port = port
        self.ssl = ssl
        self.connection_method = "smtp"
        if self.ssl == "True":
            self.connection_method = "smtp_ssl"

    def date_time(self):
        """
        Taken from logging.handlers SMTP python distribution
        
        Return the current date and time formatted for a MIME header.
        Needed for Python 1.5.2 (no email package available)
        """
        year, month, day, hh, mm, ss, wd, _, _ = time.gmtime(time.time())
        s = "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
                self.weekdayname[wd],
                day, self.monthname[month], year,
                hh, mm, ss)
        return s
        
    def getNow(self):
        try:
            from email.utils import formatdate
        except ImportError:
            formatdate = self.date_time
        return formatdate()
        
    def notify(self,message,log):
        '''msg to print, send by email, whatever...'''
        
        body = self.bodyMailAction
        if not body:
            if (message.messageLevel not in Mail.mailLevels 
                    and not message.isATarget()):
                return
            message, logpath = message.getPlainMessage()
            title = "Alert found for log "+logpath
            fancyheader = len(title)*'='
            body = fancyheader+"\n"
            body += title+"\n"
            body += fancyheader+"\n"
            body += message+"\n"

        now = self.getNow()
        
        msg = ("Subject: Log4Tailer alert\r\nFrom: %s\r\nTo: "
                "%s\r\nDate: %s\r\n\r\n" % (self.fro,self.to,now)+ body)
        timer = log.mailTimer
        try:
            if timer.awaitSend(log.triggeredNotSent):
                log.triggeredNotSent = True
                return
            self.conn.sendmail(self.fro,self.to,msg)
        except SMTPServerDisconnected:
            # server could have disconnected
            # after a long inactivity. Connect
            # again and send the corresponding 
            # alert
            self.connectSMTP()
            self.conn.sendmail(self.fro,self.to,msg)

        self.bodyMailAction = None
        log.triggeredNotSent = False
        return

    def setBodyMailAction(self,body):
        self.bodyMailAction = body
    
    def sendNotificationMail(self,body):
        '''Sends a notification mail'''
        now = self.getNow()
        msg = ("Subject: Log4Tailer Notification Message\r\nFrom: %s\r\nTo: "
                "%s\r\nDate: %s\r\n\r\n" % (self.fro,self.to,now)+ body)
        try:
            self.conn.sendmail(self.fro,self.to,msg)
        except SMTPServerDisconnected:
            self.connectSMTP()
            self.conn.sendmail(self.fro,self.to,msg)

    def _connect_smtp(self):
        conn = SMTP(self.hostname, self.port)
        return conn
    
    def _connect_smtp_ssl(self):
        print "using ssl connection"
        conn = SMTP_SSL(self.hostname, self.port)
        return conn

    def connectSMTP(self):
        connection_method = "_connect_" + self.connection_method
        conn = getattr(self, connection_method)()
        try:
            conn.connect(self.hostname, self.port)
            conn.login(self.user, self.passwd)
            print "connected"
        except Exception, ex:
            print ex
            print "Failed to connect to " + self.hostname
            sys.exit()
        self.conn = conn

    def quitSMTP(self):
        try:
            self.conn.quit()
        except:
            print "failed to quit SMTP connection"
            sys.exit()

class Filter(Print):
    """ When a pattern is found, it will notify 
    the user, otherwise nothing will be notified. It 
    would be a mix of tail and grep
    """
    def __init__(self, pattern):
        self.pattern = pattern
    
    def notify(self, message, log):
        plainMessage = message.plainMessage
        if not plainMessage:
            return
        if self.pattern.search(plainMessage):
            Print.notify(self, message, log)

class CornerMark(object):
    """Displays a 5 char colored empty string 
    at the bottom right corner of terminal in case an error, fatal or warning
    is found."""
    
    MARK = 5 * " "
    markable = {'FATAL' : 'backgroundemph', 
            'ERROR' : 'backgroundemph', 
            'WARN' : 'onyellowemph', 
            'WARNING' : 'onyellowemph',
            'TARGET' : 'oncyanemph'}

    def __init__(self, gaptime):
        self.corner_time = float(gaptime)
        self.termcolors = TermColorCodes()
        self.len_mark = len(self.MARK)
        self.timer = Timer(self.corner_time)
        self.count = 0
        self.flagged = False
        self.emphcolor = 'backgroundemph'

    def corner_mark_time(self):
        return self.corner_time

    def __term_num_cols(self):
        """Returns the number columns in the current terminal using the Linux 
        tputs command line tool.

        :return: The number of columns currently in the terminal.
        """ 
        termcols = os.popen("tput cols")
        ttcols = termcols.readline()
        termcols.close()
        ttcols = int(ttcols)
        return ttcols

    def notify(self, message, log):
        """Displays a 5 char colored empty string in case a message comes in
        with the level specified in the class attribute markable. First time we
        get a markable level, a timer is started with the number of seconds
        specified in self.corner_time and a colored string will be displayed
        for that number of seconds. The timer will not be restarted during that
        time.
        
        :param message: the message object wrapping the current log trace
        :param log: the log associated with the current message
        """ 
        level = message.messageLevel.upper()
        isTarget = message.isATarget()
        # target has priority over markable levels
        if isTarget:
            self.flagged = True
            self.emphcolor = self.markable.get("TARGET")
        elif level in self.markable:
            self.flagged = True
            self.emphcolor = self.markable.get(level)
        if self.flagged:
            if self.count == 0:
                self.timer.startTimer()
            self.count += 1
            if self.timer.corner_mark_ellapsed() < self.corner_time:
                padding = self.__term_num_cols() - self.len_mark
                trace = (padding * " " + getattr(self.termcolors,
                    self.emphcolor)+ self.MARK + self.termcolors.reset)
                print trace
            else:
                self.timer.stopTimer()
                self.count = 0
                self.flagged = False
                
                
class TriggerExecutor(threading.Thread):
    """Triggers the trigger command, one 
    trigger_command at a time, in its own thread.
    """

    def __init__(self):
        threading.Thread.__init__(self)
        self.queue = queue.Queue()
        self.go = True

    def landing(self, trigger_command):
        """One command to be triggered. Enqueued 
        to be executed when ready.
        
        :param trigger_command: command to be triggered.
        """
        self.queue.put(trigger_command)

    def run(self):
        while self.go:
            trigger_command = self.queue.get()
            if trigger_command == 'stop':
                continue
            try:
                subprocess.call(' '.join(trigger_command), shell = True)
            except Exception, err:
                print err

    def stop(self):
        self.go = False
            
class Executor(object):
    """Will execute a program if a certain condition is given"""
    PlaceHolders = '%s'
    Pullers = ['ERROR', 'FATAL', 'CRITICAL']

    def __init__(self, properties):
        executable = properties.get_value('executor')
        if not executable:
            raise Exception("need to provide executor option")
        self.executable = executable.split(' ')
        self.full_trigger_active = False
        if self.PlaceHolders in self.executable:
            self.full_trigger_active = True
        self.trigger_executor = TriggerExecutor()
        self.started = False

    def _build_trigger(self, logtrace, logpath):
        if self.full_trigger_active:
            params = [logtrace, logpath]
            trigger = []
            for param in self.executable:
                if param == self.PlaceHolders:
                    param = params.pop(0) 
                trigger.append(param)
            return trigger
        return self.executable

    def notify(self, message, log):
        msg_level = message.messageLevel.upper()
        if not message.isATarget() and msg_level not in self.Pullers:
            return
        logtrace, logpath = message.getPlainMessage()
        trigger = self._build_trigger(logtrace, logpath)
        if not self.started:
            self.started = True
            self.trigger_executor.start()
        self.trigger_executor.landing(trigger)
    
    def stop(self):
        if self.started:
            self.trigger_executor.stop()
            # unblock the queue
            self.trigger_executor.landing("stop")
            self.trigger_executor.join()
            

class Poster(object):
    """This is basically a REST client that 
    will notify a log4tailer centralized server. 
    It will register first to the server and will 
    notify it anytime an undesirable trace has been found. 
    Fatals, criticals, errors and targets will be notified.
    """ 
    Pullers = ['ERROR', 'FATAL', 'CRITICAL']

    def __init__(self, properties):
        """Instantiates a REST notifier.
        
        :param properties: a Property instance holding the necessary parameters
            to connect to the centralized server. The base_url, port, service
            uri, register and unregister uri will need to be provided in a
            configuration file.
        """ 
        self.url = properties.get_value('server_url')
        self.port = properties.get_value('server_port')
        self.service_uri = properties.get_value('server_service_uri')
        self.register_uri = properties.get_value('server_service_register_uri')
        self.unregister_uri = properties.get_value('server_service_unregister_uri')
        self.headers = {'Content-type' : 'application/json'}
        self.registered_logs = {}
        from socket import gethostname
        self.hostname = gethostname()
        # TODO should we set socket timeout?
        # socket.setdefaulttimeout(timeout)

    def notify(self, message, log):
        if log not in self.registered_logs:
            self.register(log)
        msg_level = message.messageLevel.upper()
        if not message.isATarget() and msg_level not in self.Pullers:
            return
        logtrace, _ = message.getPlainMessage()
        log_info = self.registered_logs[log]
        log_id = log_info['id']
        params = json.dumps({'logtrace': logtrace, 'loglevel' : msg_level, 
            'log': { 'id' : log_id, 'logpath' : log.path, 
                'logserver' : self.hostname}})
        response = self.send(self.service_uri, params)
        return response
    
    def register(self, log):
        params = json.dumps({'logpath': log.path, 'logserver' : self.hostname})
        response = self.send(self.register_uri, params)
        if not response:
            return
        log_id = response.read()
        self.registered_logs[log] = {'id' : log_id, 'logserver' :
                self.hostname}
        return response

    def unregister(self, log):
        if log in self.registered_logs:
            log_info = self.registered_logs[log]
            log_id = log_info['id']
            params = {'id' : log_id}
            response = self.send(self.unregister_uri, json.dumps(params))
            return response

    def send(self, uri, params):
        conn = httplib.HTTPConnection(self.url, self.port)
        try:
            conn.request('POST', uri, params, self.headers)
            response = conn.getresponse()
        except Exception, err:
            print err
            return None
        conn.close()
        return response

