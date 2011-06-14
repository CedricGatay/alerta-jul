import os
import sys
from log4tailer import LogTailer, LogColors, Log, Properties
from log4tailer import notifications
from log4tailer.utils import setup_mail
import re
import logging

__version__ = "3.0.2"
logging.basicConfig(level = logging.WARNING)
logger = logging.getLogger('log4tail')

defaults  = {'pause' : 1, 
    'silence' : False,
    'throttle' : 0,
    'actions' : [notifications.Print()],
    'nlines' : False,
    'target': None, 
    'logcolors' : LogColors.LogColors(),
    'properties' : None,
    'alt_config': os.path.expanduser('~/.log4tailer'),
    'post' : False}

def parse_config(configfile):
    properties = Properties.Property(configfile)
    properties.parse_properties()
    return properties

def initialize(options):
    logcolors = defaults['logcolors']
    actions = defaults['actions']
    config = options.configfile or defaults['alt_config']
    if options.version:
        print __version__
        sys.exit(0)
    if os.path.exists(config):
        logger.info("Configuration file [%s] found" % config)
        defaults['properties'] = parse_config(config)
        logcolors.parse_config(defaults['properties'])
    properties = defaults['properties']
    if options.pause:
        defaults['pause'] = int(options.pause)
    if options.throttle:
        throttle = float(options.throttle)
        defaults['throttle'] = throttle
    if options.silence and properties:
        mailAction = setup_mail(properties)
        actions.append(mailAction)
        defaults['silence'] = True
    if options.nomailsilence:
        # silence option with no mail
        # up to user to provide notification by mail 
        # or do some kind of reporting 
        defaults['silence'] = True
    if options.mail and properties:
        mailAction = setup_mail(properties)
        actions.append(mailAction)
    if options.filter:
        # overrides Print notifier
        actions[0] = notifications.Filter(re.compile(options.filter))
    if options.tailnlines:
        defaults['nlines'] = int(options.tailnlines)
    if options.target:
        defaults['target'] = options.target
    if options.inactivity:
        inactivityAction = notifications.Inactivity(options.inactivity, 
                properties)
        if inactivityAction.getNotificationType() == 'mail':
            if options.mail or options.silence:
                inactivityAction.setMailNotification(actions[len(actions)-1])
            else:
                mailAction = setup_mail(properties)
                inactivityAction.setMailNotification(mailAction)
        actions.append(inactivityAction)
    if options.cornermark:
        cornermark = notifications.CornerMark(options.cornermark)
        actions.append(cornermark)
    if options.post and properties:
        defaults['post'] = True
        poster = notifications.Poster(properties)
        actions.append(poster)
    if options.executable and properties:
        executor = notifications.Executor(properties)
        actions.append(executor)
    if options.screenshot and properties:
        printandshoot = notifications.PrintShot(properties)
        actions[0] = printandshoot

def monitor(options, args):
    if options.remote:
        from log4tailer import SSHLogTailer
        tailer = SSHLogTailer.SSHLogTailer(defaults)
        if not tailer.sanityCheck():
            print "missing config file parameters"
            sys.exit()
        tailer.createCommands()
        try:
            tailer.createChannels()
        except Exception,e:
            print "Could not connect"
            print "Trace [%s]" % e
            sys.exit()
        tailer.tailer()
        sys.exit()
    tailer = LogTailer.LogTailer(defaults)

    if args[0] == '-':
        tailer.pipeOut()
        sys.exit()
    for i in args:
        log = Log.Log(i,defaults['properties'],options)
        tailer.addLog(log)
    if defaults.get('nlines', None):
        try:
            tailer.printLastNLines(defaults['nlines'])
            print "Ended log4tailer, because colors are fun"
            sys.exit()
        except KeyboardInterrupt:
            print "Ended log4tailer, because colors are fun"
            sys.exit()
    tailer.tailer()

def main(options, args):
    initialize(options)
    monitor(options, args)
