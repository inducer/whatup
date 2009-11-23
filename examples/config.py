# -----------------------------------------------------------------------------
# whatup sample configuration
# -----------------------------------------------------------------------------
# Copy to ~/.config/whatup/config.py
# -----------------------------------------------------------------------------

class DefaultClassifier:
    max_duration = 70
    default_ignore_set = set(["idle"])

    def __call__(self, sample):
        focused = sample.focused_window
        if not focused:
            yield "idle"
            return

        import re
        if sample.idletime > 60:
            yield "idle"

        productive = "no"

        # projects
        work_match = re.search("~/work/([^/]+)", focused.title)
        if work_match:
            yield Category("project", work_match.group(1))
            productive = "maybe"
        elif "~/src" in focused.title:
            yield Category("project", "hedge")
            productive = "yes"
        elif "~/research/job-search" in focused.title:
            yield Category("project", "job-search")
            productive = "yes"
        elif "~/research/thesis" in focused.title:
            yield Category("project", "thesis")
            productive = "yes"
        elif "~/research/writeups" in focused.title:
            yield Category("project", "paper")
            productive = "yes"

        if focused.program in ["okular", "evince"]:
            productive = "yes"

        if "Navigator" in focused.program:
            # web
            if "Synoptic" in focused.title:
                productive = "yes"
                yield "synoptic"

            if "SPIEGEL" in focused.title:
                yield "spiegel"

            if "Google Reader" in focused.title:
                yield "rss"

            yield "web"

        if "kontact" in focused.program:
            yield "mail"
            productive = "maybe"

        if "konsole" in focused.program:
            yield "shell"
            if productive == "no":
                productive = "maybe"

        if "gvim" in focused.program:
            yield "edit"
            if productive == "no":
                productive = "maybe"

        yield Category("prg", focused.program)
        yield Category("productive", productive)
        yield Category("host", sample.hostname)
