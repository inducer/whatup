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
        work_match = re.search("~/work/([^/]+)", focused.detail)
        if work_match:
            yield Category("project", work_match.group(1))
            productive = "maybe"
        elif "~/src" in focused.detail:
            yield Category("project", "hedge")
            productive = "yes"
        elif "~/research/job-search" in focused.detail:
            yield Category("project", "job-search")
            productive = "yes"
        elif "~/research/thesis" in focused.detail:
            yield Category("project", "thesis")
            productive = "yes"
        elif "~/research/writeups" in focused.detail:
            yield Category("project", "paper")
            productive = "yes"

        if focused.group in ["okular", "evince"]:
            productive = "yes"

        if "Navigator" in focused.group:
            yield "web"

            url_item = sample.focused_url

            if "Synoptic" in focused.detail:
                productive = "yes"
                yield "synoptic"
            elif url_item is not None:
                url = url_item.detail

                from urlparse import urlparse
                yield Category("site", urlparse(url).netloc)

                if "google.com/reader" in url:
                    yield "rss"

                elif "google.com/search" in url:
                    productive = "maybe"
                    yield "websearch"

                elif "docs.python.org" in url:
                    productive = "maybe"
                    yield "documentation"
                elif "documen.tician.de" in url:
                    productive = "yes"
                    yield "documentation"

                #literature
                elif "google.com/scholar" in url:
                    productive = "yes"
                    yield "literature"
                elif "arxiv.org" in url:
                    productive = "yes"
                    yield "literature"
                elif "sciencedirect.com" in url:
                    productive = "yes"
                    yield "literature"
                elif "jstor.org" in url:
                    productive = "yes"
                    yield "literature"

                # job search
                elif "mathjobs.org" in url:
                    productive = "yes"
                    yield Category("project", "job-search")

        if "kontact" in focused.group:
            yield "mail"
            productive = "maybe"

        if "konsole" in focused.group:
            yield "shell"
            if productive == "no":
                productive = "maybe"

        if "gvim" in focused.group:
            yield "edit"
            if productive == "no":
                productive = "maybe"

        yield Category("prg", focused.group)
        yield Category("productive", productive)
        yield Category("host", sample.hostname)
