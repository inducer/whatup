class CaptureLock(object):
    def __init__(self, db):
        self.lock_file = db.name + ".capture-lock"

    def __enter__(self):
        import os
        try:
            self.fd = os.open(self.lock_file,
                    os.O_CREAT | os.O_WRONLY | os.O_EXCL)
        except OSError:
            raise RuntimeError(
                    "could not obtain capture lock--delete '%s' if necessary"
                    % self.lock_file)

        return self

    def __exit__(self, type, value, traceback):
        import os
        os.close(self.fd)
        os.unlink(self.lock_file)




def run_capture(db, interval=60):
    from Xlib import display, Xatom
    from Xlib.xobject.drawable import Window as X11Window
    import Xlib.protocol.rq as rq
    import whatup.xss as xss

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

    from whatup.datamodel import Sample, Window
    while True:
        windows = root.get_full_property(client_list_atom, Xatom.WINDOW).value

        focus_id = dpy.get_input_focus().focus.id

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

        for wid in windows:
            x11win = X11Window(dpy.display, wid)
            focused_subwin = follow_tree_until(x11win, lambda subwin: subwin.id == focus_id)
            is_focused = focused_subwin is not None

            title = unicode(get_name(x11win))
            dbwin = Window(
                    sample=smp,
                    title=title,
                    program=unicode(x11win.get_wm_class()[0]),
                    focused=is_focused)

        session.add(smp)
        session.commit()

        time.sleep(interval)
