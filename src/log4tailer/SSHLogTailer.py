import os
import sys
import logging
import getpass
import time
import select
from log4tailer.Log import Log
from log4tailer.Message import Message
from log4tailer.TermColorCodes import TermColorCodes
from subprocess import Popen, PIPE
import notifications

try:
    import paramiko
except:
    print "You need to install paramiko module"
    sys.exit()

SSH_DIR = os.path.join(os.path.expanduser('~'),'.ssh')
SSH_KEY = os.path.join(SSH_DIR, 'id_rsa')

class SSHLogTailer(object):
    
    HOSTNAME_PROPERTY_PREFIX = "hostname "
    TAIL_COMMAND_PREFIX = "tail -F "

    def __init__(self, defaults):
        self.arrayLog = []
        self.logcolors = defaults['logcolors']
        self.pause = defaults['pause']
        self.silence = defaults['silence']
        self.actions = notifications.Print()
        self.throttleTime = defaults['throttle'] 
        self.target = defaults['target']
        self.properties = defaults['properties']
        self.mailAction = None
        self.logger = logging.getLogger('SSHLogTailer')
        self.sshusername = None
        self.hostnames = {}
        self.hostnameChannels = {}
        self.color = TermColorCodes()
        self.rsa_key = SSH_KEY

    def sanityCheck(self):
        hostnamescsv = self.properties.get_value('sshhostnames')
        if not hostnamescsv:
            self.logger.error("sshhostnames should be provided "
                              "in configfile for ssh tailing")
            return False
        hostnames = [hostname.strip() for hostname in hostnamescsv.split(',')]
        for hostname in hostnames:
            self.logger.debug("hostname [%s] found in config file" % hostname)
            hostnameValues = self.properties.get_value(hostname)
            if not hostnameValues:
                self.logger.debug("values for hostname [%s] are [%s]" % (
                    hostname,self.properties.get_value(hostname)))
                self.logger.error("missing username and logs for [%s]" % (
                                  hostname))
                return False
            hostnameProperties = [props.strip() for props in 
                                  hostnameValues.split(',')]
            username = hostnameProperties[0]
            self.hostnames[hostname] = {} 
            hostnameDict = self.hostnames[hostname]
            hostnameDict['username'] = username
            self.logger.debug("hostname [%s] has username [%s]" % (
                              hostname, username))
            hostnameDict['logs'] = []
            for log in hostnameProperties[1:]:
                self.logger.debug("log [%s] for hostname [%s] found" % (log,
                                  hostname))
                hostnameDict['logs'].append(log.strip())
            self.logger.debug("logs for hostname [%s] are [%s]" % (hostname, 
                              hostnameDict['logs']))
        rsa_key = self.properties.get_value('rsa_key')
        if rsa_key:
            print "rsa key provided: "+rsa_key
            self.rsa_key = rsa_key
        return True

    def createCommands(self):
        for hostname in self.hostnames.keys():
            command = SSHLogTailer.TAIL_COMMAND_PREFIX + \
                    ' '.join(self.hostnames[hostname]['logs'])
            self.hostnames[hostname]['command'] = command
            self.logger.debug("hostname information [%s]" % (
                              self.hostnames[hostname]))

    def getChannelTransport(self, sshclient, hostname):
        transport = sshclient.get_transport()
        sshChannel = transport.open_session()
        self.hostnameChannels[hostname] = {}
        self.hostnameChannels[hostname]['channel'] = sshChannel
        self.hostnameChannels[hostname]['client'] = sshclient
 
    def createChannels(self):
        passwordIsSame = False
        passwordhost = None
        count = 0
        hostnames = self.hostnames.keys()
        numHosts = len(hostnames)
        announceOneTime = 0
        for hostname in hostnames:
            sshclient = paramiko.SSHClient()
            sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            hostusername = self.hostnames[hostname]['username']
            try:
                sshclient.connect(hostname, username=hostusername, 
                        key_filename=self.rsa_key)
                self.getChannelTransport(sshclient, hostname)
                continue
            except Exception, err:
                if announceOneTime ==  0:
                    announceOneTime += 1
                    self.logger.warning(err)
            if not passwordIsSame:
                print "Password for host %s?" % hostname
                passwordhost = getpass.getpass()
            sshclient.connect(hostname,username=hostusername,
                              password=passwordhost)
            if count == 0 and numHosts > 1:
                answer = raw_input("Is this password the same for all " 
                                   "hosts (Y/n)?\n")
                if answer == 'n' or answer == 'N':
                    passwordIsSame = False
                else:
                    passwordIsSame = True
                count += 1
            self.getChannelTransport(sshclient, hostname)
    
    def __hostnameChangedHeader(self,hostname):
        tputcommand = ["tput","cols"]
        numColsproc = Popen(tputcommand,stdout=PIPE)
        numCols = numColsproc.communicate()[0].rstrip()
        lenhost = len(hostname)
        fancyWidth = (int(numCols)-lenhost-2)/2
        fancyheader = '*' * fancyWidth
        hostnameHeader = (self.color.green +  # pylint: disable-msg=E1101
                fancyheader + ' ' + 
                hostname + ' ' + 
                fancyheader + 
                self.color.reset) 
        print hostnameHeader

    def tailer(self):
        '''Stdout multicolor tailer'''
        message = Message(self.logcolors,self.target,self.properties)
        anylog = Log('anylog')
        for hostname in self.hostnames.keys():
            command = self.hostnames[hostname]['command']
            self.logger.debug("command [%s] to be executed in host [%s]" % (
                              command,hostname))
            self.hostnameChannels[hostname]['channel'].exec_command(command)
        try:
            lasthostnameChanged = ""
            while True:
                for hostname in self.hostnames.keys():
                    sshChannel = self.hostnameChannels[hostname]['channel']
                    rr, _, _ = select.select([sshChannel],[],[],0.0)
                    if len(rr)>0:
                        lines = sshChannel.recv(4096).split('\n')
                        if hostname != lasthostnameChanged:
                            self.__hostnameChangedHeader(hostname)
                        for line in lines:
                            message.parse(line, anylog)
                            self.actions.notify(message, anylog)
                        lasthostnameChanged = hostname
                time.sleep(1)
        except:
            print "\nfinishing ..."
            for hostname in self.hostnames.keys():
                sshChannel = self.hostnameChannels[hostname]['channel']
                sshclient = self.hostnameChannels[hostname]['client']
                command = self.hostnames[hostname]['command']
                procidCommand = 'pgrep -f -x '+'\"'+command+'\"'
                self.logger.debug("procid command [%s]" % procidCommand)
                sshChannel.close()
                stdin,stdout,stderr = sshclient.exec_command(procidCommand)
                res = stdout.readlines()
                if res:
                    procid = res[0].rstrip()
                    self.logger.debug("procid [%s]" % procid)
                    # is process still alive after closing channel?
                    if procid:
                        # kill it
                        killprocid = 'kill -9 '+procid
                        stdin,stdout,stderr = sshclient.exec_command(killprocid)
                #sshChannel.shutdown(2)
                sshclient.close()
            print "Ended log4tailer, because colors are fun"
            sys.exit()


