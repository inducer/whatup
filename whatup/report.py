def print_sample(sample):
    import time

    print "At %s our time in timezone %s (offset %g h vs here):" % (
            time.ctime(sample.timestamp),
            sample.timezonename,
            (sample.timezoneoffset-time.timezone)/3600)

    if sample.idletime < 60*1000:
        print "    Idle time: %g seconds" % (sample.idletime / 1000)
    else:
        print "    Idle time: %g minutes" % (sample.idletime / (1000*60))
    print "    Host: %s" % sample.hostname
    print

    for win in sample.windows:
        s = "'%s' (program %s)" % (win.title, win.program)
        if win.focused:
            s = "FOCUSED " + s
        else:
            s = "  " + s
        print "    "+s
    print






def dump_database(db):
    session = db.sessionmaker()

    from whatup.datamodel import Sample
    for sample in session.query(Sample):
        print_sample(sample)




class Category:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return "%s:%s" % (self.name, self.value)




def format_duration(seconds):
    if seconds > 24*3600:
        return "%dd %dh" % (
                seconds // (24*3600),
                seconds % (24*3600) // 3600)
    elif seconds > 3600:
        return "%dh%02dm" % (
                seconds // 3600,
                seconds % 3600 // 60)
    else:
        return "%dm%02ds" % (
                seconds // 60,
                seconds % 60)




def format_histogram(tags_and_amounts, total, use_unicode=True, width=70):
    from math import floor, ceil
    if use_unicode:
        def format_bar(amt):
            scaled = amt*width/max_amount
            full = int(floor(scaled))
            eighths = int(ceil((scaled-full)*8))
            if eighths:
                return full*unichr(0x2588) + unichr(0x2588+(8-eighths))
            else:
                return full*unichr(0x2588)
    else:
        def format_bar(amt):
            return int(ceil(amt*width/max_amount))*"#"

    max_amount = max(c for t, c in tags_and_amounts)

    print "\n".join("%15s | %3.0f%% | %9s | %s" % (
        name,
        amount/total*100,
        format_duration(amount),
        format_bar(amount))
        for name, amount in tags_and_amounts)




def run_classifier(db, classifier):
    session = db.sessionmaker()

    total_time = 0
    classified_time = 0
    classified_samples = 0

    last_timestamp = None
    max_duration = getattr(classifier, "max_duration", 70)

    bins = {}
    cat_bins = {}

    from whatup.datamodel import Sample
    for sample in session.query(Sample).order_by(Sample.timestamp):

        if last_timestamp is None:
            sample_duration = 0
        else:
            sample_duration = sample.timestamp - last_timestamp

        total_time += sample_duration

        tag_count = 0
        tag_names = set()
        for tag in classifier(sample):
            tag_count += 1

            bins[str(tag)] = bins.get(str(tag), 0) + sample_duration

            if isinstance(tag, Category):
                tag = tag.name
            assert tag not in tag_names, \
                    "Double-tagging occurred for tag '%s'" % tag
            tag_names.add(tag)

        if tag_count:
            classified_time += sample_duration
            classified_samples += 1

        last_timestamp = sample.timestamp

    sample_count = session.query(Sample).count()

    if sample_count:
        first_time = (session.query(Sample.timestamp)
                .order_by(Sample.timestamp)[0])[0]
        last_time = (session.query(Sample.timestamp)
                .order_by(Sample.timestamp.desc())[0])[0]
        data_period = last_time-first_time

    bins = sorted(bins.iteritems())
    format_histogram(bins, total_time)
    print
    if total_time:
        print "Data period:      %s" % format_duration(data_period)
        print "Time sampled:     %s (%.1f %% of period, %d samples) " % (
                format_duration(total_time),
                total_time/data_period*100,
                sample_count)
        print "Time classified:  %s (%.1f %% of sampled, %d samples) " % (
                format_duration(classified_time),
                classified_time/total_time*100,
                classified_samples)




def run_classifier_by_name(db, config_file, classifier, args):
    ex_globals = {
        "Category": Category
        }
    execfile(config_file, ex_globals)

    run_classifier(db, ex_globals[classifier](**args))
