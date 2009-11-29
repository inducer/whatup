class DatabaseLock(object):
    def __init__(self, db):
        self.lock_file = db.name + ".whatup-lock"

    def __enter__(self):
        import os
        try:
            self.fd = os.open(self.lock_file,
                    os.O_CREAT | os.O_WRONLY | os.O_EXCL)
        except OSError:
            raise RuntimeError(
                    "could not obtain database lock--delete '%s' if necessary"
                    % self.lock_file)

        return self

    def __exit__(self, type, value, traceback):
        import os
        os.close(self.fd)
        os.unlink(self.lock_file)




def run_capture(db, interval, mozrepl_port):
    from Xlib import display, Xatom
    from Xlib.xobject.drawable import Window
    import Xlib.protocol.rq as rq
    import whatup.xss as xss
    import netifaces
    import socket
    import telnetlib

    dpy = display.Display()

    root = dpy.screen().root

    client_list_atom = dpy.intern_atom("_NET_CLIENT_LIST")
    name_atom = dpy.intern_atom("_NET_WM_NAME")
    utf8_string = dpy.intern_atom("UTF8_STRING")

    def follow_tree_until(win, pred, level=0):
        if pred(win):
            return win

        for subwin in win.query_tree().children:
            return follow_tree_until(subwin, pred, level+1)

        return None

    def get_name(win):
        try:
            name = win.get_full_property(name_atom, utf8_string).value
        except:
            return win.get_wm_name()
        else:
            return name.decode("utf8")

    def get_idle_time():
        try:
            xss_info = xss.query_info(dpy, root)
            return xss_info.idle/1000
        except:
            return None

    import time

    from socket import gethostname
    hostname = gethostname()

    from whatup.datamodel import Sample, SampleItem
    while True:
        windows_reply = root.get_full_property(client_list_atom, Xatom.WINDOW)
        if windows_reply is not None:
            windows = windows_reply.value
        else:
            import sys
            print>>sys.stderr, "WARNING: _NET_CLIENT_LIST not present"
            windows = []

        focus_win = dpy.get_input_focus().focus
        if isinstance(focus_win, Window):
            focus_id = focus_win.id
        else:
            import sys
            print>>sys.stderr, "WARNING: no focused window found"
            focus_id = None

        secs = time.time()
        localtime = time.localtime(secs)

        if localtime.tm_isdst:
            tzname = time.tzname[1]
        else:
            tzname = time.tzname[0]

        session = db.sessionmaker()
        smp = Sample(
                timestamp=secs,
                timezoneoffset=time.timezone,
                timezonename=unicode(tzname),
                hostname=hostname,
                idletime=get_idle_time())

        # capture X11 windows -------------------------------------------------
        for wid in windows:
            x11win = Window(dpy.display, wid)
            focused_subwin = follow_tree_until(x11win, lambda subwin: subwin.id == focus_id)
            is_focused = focused_subwin is not None

            if is_focused:
                what = "focused-window"
            else:
                what = "window"

            title = unicode(get_name(x11win))
            SampleItem(sample=smp,
                    what=what,
                    group=unicode(x11win.get_wm_class()[0]),
                    detail=title,
                    session=session)

        # capture interface addresses -----------------------------------------
        for iface_name in netifaces.interfaces():
            if iface_name.startswith("lo") or iface_name.startswith("pan"):
                continue

            for addr_dict in netifaces.ifaddresses(iface_name).get(socket.AF_INET, []):
                if "addr" in addr_dict:
                    SampleItem(sample=smp,
                            what="inet-addr",
                            group=unicode(iface_name),
                            detail=unicode(addr_dict["addr"]),
                            session=session)

        # capture firefox tabs ------------------------------------------------
        # uses mozrepl, http://wiki.github.com/bard/mozrepl

        try:
            mozrepl = telnetlib.Telnet("localhost", mozrepl_port)
        except socket.error:
            from warnings import warn
            warn("could not connect to mozrepl")
        else:
            try:
                mozrepl.read_until("repl>")
                mozrepl.write("{"
                        "var num = gBrowser.browsers.length;"
                        "for (var i = 0; i < num; i++)"
                        "{"
                        "  var b= gBrowser.getBrowserAtIndex(i); "
                        "  try { repl.print(b.currentURI.spec); } catch (e) {}"
                        "}}")
                all_tabs = (mozrepl.read_until("repl>")
                        .replace("repl>", "")
                        .strip()
                        .strip('"').split("\n"))

                mozrepl.write("content.location.href;")
                current_tab = (mozrepl.read_until("repl>")
                        .replace("repl>", "")
                        .strip()
                        .strip('"'))
                mozrepl.write("repl.quit();")

            finally:
                mozrepl.close()

            for tab in all_tabs:
                if tab == current_tab:
                    what = "focused-moz-tab"
                else:
                    what = "moz-tab"

                SampleItem(sample=smp,
                        what=what,
                        group=unicode("mozilla"),
                        detail=unicode(tab),
                        session=session)

        # commit sample -------------------------------------------------------
        session.add(smp)
        session.commit()

        time.sleep(interval)
