MAPPERS_DEFINED = [False]




class DataModel(object):
    def __init__(self):
        if MAPPERS_DEFINED[0]:
            return

        MAPPERS_DEFINED[0] = True

        from sqlalchemy import Table, Column, \
                Integer, Float, Text, UnicodeText, Boolean, Unicode, ForeignKey, \
                MetaData, Index

        cls = DataModel

        cls.metadata = MetaData()

        cls.sample = Table('sample', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('timestamp', Float, index=True),
                Column('timezoneoffset', Float),
                Column('timezonename', UnicodeText()),
                Column('hostname', Text()),
                Column('idletime', Float),
                )

        cls.item_data = Table('item_data', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('what', Text()),
                Column('group', UnicodeText()),
                Column('detail', UnicodeText()),
                )

        cls.sample_item = Table('sample_item', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('sample_id', Integer, ForeignKey('sample.id'), index=True),
                Column('item_data_id', Integer, ForeignKey('item_data.id'), index=True),
                )

        Index("sample_props", 
                cls.item_data.c.what,
                cls.item_data.c.group,
                cls.item_data.c.detail,
                unique=True)

        from sqlalchemy.orm import mapper, relation

        mapper(Sample, cls.sample, properties={
            'items': relation(SampleItem, backref='sample',
                cascade="all, delete, delete-orphan"),
            })
        mapper(ItemData, cls.item_data, properties={
            'sample_items': relation(SampleItem, backref='data',
                cascade="all, delete, delete-orphan"),
            })
        mapper(SampleItem, cls.sample_item)




# mapped instances ------------------------------------------------------------
class Sample(object):
    def __init__(self, timestamp, timezoneoffset, timezonename, hostname, idletime):
        self.timestamp = timestamp
        self.timezoneoffset = timezoneoffset
        self.timezonename = timezonename
        self.hostname = hostname
        self.idletime = idletime

    def duplicate(self, tgt_session):
        result = Sample(
            self.timestamp,
            self.timezoneoffset,
            self.timezonename,
            self.hostname,
            self.idletime,
            )
        for s in self.items:
            result.items.append(w.duplicate(tgt_session))
        return result

    @property
    def focused_window(self):
        for i in self.items:
            if i.data.what == "focused-window":
                return i

    @property
    def focused_url(self):
        for i in self.items:
            if i.data.what == "focused-moz-tab":
                return i


    def __unicode__(self):
        return self.stringify()

    def stringify(self, tags=None):
        import time

        lines = ["At %s our time in timezone %s (offset %g h vs here):" % (
                time.ctime(self.timestamp),
                self.timezonename,
                (self.timezoneoffset-time.timezone)/3600)]

        if self.idletime < 60:
            lines.append("    Idle time: %g seconds" % self.idletime)
        else:
            lines.append("    Idle time: %g minutes" % (self.idletime/60))

        lines.append("    Host: %s" % self.hostname)
        if tags:
            lines.append("    Tags: %s" % ",".join(str(tag) for tag in tags))
        lines.append("")

        for item in self.items:
            lines.append("    "+unicode(item))
        return u"\n".join(lines)




class SampleItem(object):
    def __init__(self, sample, what=None, group=None, detail=None, session=None):
        if sample is not None:
            self.sample = sample

        if what is not None:
            assert session is not None
            self.data = make_item_data(session, what, group, detail)

    def duplicate(self, tgt_session):
        result = SampleItem(
                None,
                self.what,
                self.group,
                self.detail,
                tgt_session)
        return result

    @property
    def detail(self):
        return self.data.detail

    @property
    def what(self):
        return self.data.what

    @property
    def group(self):
        return self.data.group

    def __unicode__(self):
        return u"%s '%s' (group %s)" % (self.what, self.detail, self.group)



class ItemData(object):
    def __init__(self, what, group, detail):
        self.what = what
        self.group = group
        self.detail = detail




def make_item_data(session, what, group, detail):
    qry = (session.query(ItemData)
            .filter(ItemData.what==what)
            .filter(ItemData.group==group)
            .filter(ItemData.detail==detail))

    if qry.count() == 1:
        return qry.one()
    else:
        return ItemData(what, group, detail)




# fetching --------------------------------------------------------------------
def fetch_records(tgt_db, src_db):
    tgt_session = tgt_db.sessionmaker()
    src_session = src_db.sessionmaker()

    for sample in src_session.query(Sample).order_by(Sample.timestamp):
        src_session.delete(sample)
        tgt_session.add(sample.duplicate(tgt_session))
    src_session.commit()
    tgt_session.commit()
