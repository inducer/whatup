# -----------------------------------------------------------------------------
# whatup sample configuration
# -----------------------------------------------------------------------------
# Copy to ~/.config/whatup/config.py
# -----------------------------------------------------------------------------

class DefaultClassifier:
    max_duration = 70

    def __call__(self, sample):
        if sample.idletime > 60:
            return

        focused = sample.focused_window
        if not focused:
            return

        if "Navigator" in focused.program:
            # web
            if "SPIEGEL" in focused.title:
                yield Category("kind", "waste")
                yield "spiegel"

            if "Google Reader" in focused.title:
                yield Category("kind", "waste")
                yield "rss"

            yield "web"

        yield Category("host", sample.hostname)

        if "konsole" in focused.program:
            yield "shell"

        if "gvim" in focused.program:
            yield "edit"
