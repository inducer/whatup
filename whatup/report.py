def dump_database(db, classifier=None):
    session = db.sessionmaker()

    from whatup.datamodel import Sample
    from sqlalchemy.orm import eagerload

    for sample in session.query(Sample).options(eagerload("windows")):
        print sample.stringify(classifier)
        print





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
            if max_amount != 0:
                scaled = amt*width/max_amount
            else:
                scaled = 0

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

    print "\n".join("%20s | %3.0f%% | %9s | %s" % (
        name,
        amount/total*100 if total != 0 else 0,
        format_duration(amount),
        format_bar(amount))
        for name, amount in tags_and_amounts)




def run_classifier(db, classifier, ignore=None, only=set(),
        show_unclassified=False):
    session = db.sessionmaker()

    total_time = 0
    classified_time = 0
    classified_samples = 0
    ignored_time = 0
    ignored_samples = 0

    last_timestamp = None
    max_duration = getattr(classifier, "max_duration")

    if ignore is None:
        ignore = getattr(classifier, "default_ignore_set", set())

    bins = {}
    cat_bins = {}

    from whatup.datamodel import Sample
    from sqlalchemy.orm import eagerload
    for sample in (session.query(Sample)
            .options(eagerload("windows"))
            .order_by(Sample.timestamp)):

        if last_timestamp is None:
            sample_duration = 0
        else:
            sample_duration = sample.timestamp - last_timestamp

        if max_duration is not None:
            sample_duration = min(max_duration, sample_duration)

        total_time += sample_duration

        tag_names = set()
        tags = []
        for tag in classifier(sample):
            if isinstance(tag, Category):
                tag_name = tag.name
            else:
                tag_name = tag

            assert tag not in tag_names, \
                    "Double-tagging occurred for tag '%s'" % tag

            tag_names.add(tag_name)
            tags.append(tag)

        if tag_names and not (tag_names & ignore):
            successful_tags = 0
            for tag in tags:
                if isinstance(tag, Category):
                    tag_name = tag.name
                else:
                    tag_name = tag

                if not only or tag_name in only or str(tag) in only:
                    bins[str(tag)] = bins.get(str(tag), 0) + sample_duration
                    successful_tags += 1

            if not successful_tags and show_unclassified:
                print sample.stringify(classifier)

            classified_time += sample_duration
            classified_samples += 1
        else:
            ignored_time += sample_duration
            ignored_samples += 1

        last_timestamp = sample.timestamp

    if not show_unclassified:
        if not bins:
            print "no matching events"
            return

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
            print "Time sampled:     %s (%.1f%% of period, %d samples) " % (
                    format_duration(total_time),
                    total_time/data_period*100,
                    sample_count)
            print "Time classified:  %s (%.1f%% of sampled, %d samples) " % (
                    format_duration(classified_time),
                    classified_time/total_time*100,
                    classified_samples)
            print "Time ignored:     %s (%.1f%% of sampled, %d samples) " % (
                    format_duration(ignored_time),
                    ignored_time/total_time*100,
                    ignored_samples)




def make_classifier(config_file, classifier, args):
    ex_globals = {
        "Category": Category
        }
    execfile(config_file, ex_globals)

    return ex_globals[classifier](**args)
