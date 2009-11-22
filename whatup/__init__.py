from __future__ import division
from __future__ import with_statement




def get_data_path():
    import os.path

    home = os.environ.get('HOME', '/')
    xdg_data_home = os.environ.get('XDG_DATA_HOME',
            os.path.join(home, '.local', 'share'))

    whatup_path = os.path.join(xdg_data_home, "whatup")
    if os.path.isdir(whatup_path):
        return whatup_path
    else:
        os.makedirs(whatup_path)
        return whatup_path

def get_user_config_path():
    import os.path
    home = os.environ.get('HOME', '/')
    return os.environ.get('XDG_CONFIG_HOME',
                os.path.join(home, '.config'))

def get_config_paths():
    import os.path

    return [get_user_config_path()] + \
        os.environ.get('XDG_CONFIG_DIRS', '/etc/xdg').split(':')

def add_my_config_path(p):
    import os.path
    return os.path.join(p, "whatup", "config.py")





class Database(object):
    def __init__(self, name=None):
        import os.path
        if name is None:
            name = os.path.join(
                    get_data_path(),
                    "whatup.sqlite")

        self.name = name
        from sqlalchemy import create_engine
        self.engine = create_engine("sqlite:///"+name)
        from whatup.datamodel import DataModel
        self.datamodel = DataModel()
        self.datamodel.metadata.create_all(self.engine)

        from sqlalchemy.orm import sessionmaker
        self.sessionmaker = sessionmaker(bind=self.engine,
                autoflush=True,
                autocommit=False)





class Log:
    """file-like for writes with auto flush after each write
    to ensure that everything is logged, even during an
    unexpected exit."""

    def __init__(self, f):
        self.f = f
    def write(self, s):
        self.f.write(s)
        self.f.flush()
    def flush(self):
        self.f.flush()




def daemonize(pidfile, logfile):
    import os
    import sys

    # do the UNIX double-fork magic, see Stevens' "Advanced
    # Programming in the UNIX Environment" for details (ISBN 0201563177)
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError, e:
        print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    # decouple from parent environment
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent
            open(pidfile,'w').write("%d" % pid)
            sys.exit(0)

    except OSError, e:
        print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    sys.stdout = sys.stderr = Log(open(logfile, 'a+'))

    sys.stderr.write("starting whatup with pid %d\n" % os.getpid())




def main():
    import sys
    import os
    import os.path
    from optparse import OptionParser

    description = """
    COMMAND may be one of 'capture', 'dump', 'stop', 'report', 
    'fetch <otherdb>'.
    """


    parser = OptionParser(usage="%prog [OPTIONS] COMMAND [ARGS]",
            description=description)

    parser.add_option("--interval", type="float", metavar="SECONDS",
            default=60, help="Sample capture interval")
    parser.add_option("--db", metavar="DB_FILE",
            help="Use database file DB_FILE")
    parser.add_option("-d", "--daemon",
            help="Fork capture daemon into background",
            action="store_true")
    parser.add_option(
            "--config", 
            help="Configuration file", metavar="CONFIG.PY")
    parser.add_option(
            "--pidfile",
            default=os.path.join(get_data_path(), "whatup.pid"),
            help="PID file for daemonization", metavar="PIDFILE")
    parser.add_option(
            "-l", "--logfile", 
            default=os.path.join(get_data_path(), "whatup.log"),
            help="Log file for daemonization", metavar="LOGFILE")
    parser.add_option(
            "-a", "--classifier-args", 
            metavar="KEY=VALUE,KEY=VALUE")
    parser.add_option(
            "-c", "--classifier", 
            metavar="CLASSIFIER_CLASS",
            help="Which classifier class to use from your config file. "
            "Defaults to 'DefaultClassifier'.",
            default="DefaultClassifier")
    parser.add_option("-i", "--ignore", metavar="TAG,TAG", help="Ignore samples with these tags.")
    parser.add_option("-o", "--only", metavar="TAG,TAG", help="Only show these tags.")
    parser.add_option("-u", "--show-unclassified", action="store_true", 
            help="Show un-ignored, unclassified sample events.")
    options, args = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        sys.exit(1)

    cmd = args[0]

    def get_config_file():
        config_file = options.config

        if config_file is None:
            for p in get_config_paths():
                fn = add_my_config_path(p)
                if os.path.exists(fn):
                    config_file = fn
                    break

        return config_file


    def make_classifier(config_file):
        from whatup.report import make_classifier

        args = {}
        if options.classifier_args:
            for arg in options.classifier_args.split(","):
                equal_idx = arg.find("=")
                if equal_idx == -1:
                    args[arg] = True
                else:
                    args[arg[:equal_idx]] = arg[equal_idx+1:]

        return make_classifier(config_file, options.classifier, args)

    if cmd == "capture":
        db = Database(options.db)

        from whatup.capture import run_capture, CaptureLock
        if options.daemon:
            with CaptureLock(db) as cl:
                # make sure we can get it to catch user mistakes,
                # 'real' lock occurs later
                pass

            daemonize(options.pidfile, options.logfile)

            try:
                with CaptureLock(db) as cl:
                    run_capture(db, options.interval)
            finally:
                os.unlink(options.pidfile)

        else:
            with CaptureLock(db) as cl:
                run_capture(db, options.interval)

    elif cmd == "dump":
        from whatup.report import dump_database
        config_file = get_config_file()
        if config_file is not None:
            classifier = make_classifier(config_file)
        else:
            classifier = None

        dump_database(Database(options.db), classifier)

    elif cmd == "stop":
        with open(options.pidfile, "r") as pidf:
            from signal import SIGINT
            os.kill(int(pidf.read()), SIGINT)

    elif cmd == "report":
        config_file = get_config_file()

        if config_file is None:
            raise RuntimeError("you need to create a classifier file in '%s'"
                    % add_my_config_path(get_user_config_path()))

        db = Database(options.db)

        ignore = None
        if options.ignore:
            ignore = set(options.ignore.split(","))

        only = set()
        if options.only:
            only = set(options.only.split(","))

        from whatup.report import run_classifier
        run_classifier(db, make_classifier(config_file),
                ignore, only, show_unclassified=options.show_unclassified)

    elif cmd == "fetch":
        if len(args) < 2:
            print>> sys.stderr, "no source database specified"
            sys.exit(1)

        from whatup.datamodel import fetch_records
        fetch_records(Database(options.db), Database(args[1]))

    else:
        parser.print_help()
        sys.exit(1)
