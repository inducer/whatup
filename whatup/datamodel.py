MAPPERS_DEFINED = [False]




class DataModel(object):
    def __init__(self):
        if MAPPERS_DEFINED[0]:
            return

        MAPPERS_DEFINED[0] = True

        from sqlalchemy import Table, Column, \
                Integer, Float, Text, UnicodeText, Boolean, Unicode, ForeignKey, \
                MetaData

        cls = DataModel

        cls.metadata = MetaData()

        cls.samples = Table('sample', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('timestamp', Float, index=True),
                Column('timezoneoffset', Float),
                Column('timezonename', UnicodeText()),
                Column('hostname', Text()),
                Column('idletime', Float),
                )

        cls.windows = Table('window', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('sample_id', Integer, ForeignKey('sample.id'), index=True),
                Column('title', UnicodeText()),
                Column('program', UnicodeText()),
                Column('focused', Boolean()),
                )

        from sqlalchemy.orm import mapper, relation

        mapper(Sample, self.samples, properties={
            'windows': relation(Window, backref='sample'),
            })
        mapper(Window, self.windows)




# mapped instances ------------------------------------------------------------
class Sample(object):
    def __init__(self, timestamp, timezoneoffset, timezonename, hostname, idletime):
        self.timestamp = timestamp
        self.timezoneoffset = timezoneoffset
        self.timezonename = timezonename
        self.hostname = hostname
        self.idletime = idletime

    @property
    def focused_window(self):
        for w in self.windows:
            if w.focused:
                return w




class Window(object):
    def __init__(self, sample, title, program, focused):
        self.sample = sample
        self.title = title
        self.program = program
        self.focused = focused
