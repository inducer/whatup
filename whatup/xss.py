# Xlib.ext.xtest -- XTEST extension module
#
#    based on code
#    Copyright (C) 2009 Andreas Kloeckner <inform@tiker.net>
#    Copyright (C) 2000 Peter Liljenberg <petli@ctrl-c.liu.se>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from Xlib import X
from Xlib.protocol import rq

extname = "MIT-SCREEN-SAVER"

PropertyName = "_MIT_SCREEN_SAVER_ID"

NotifyMask = 0x00000001
CycleMask = 0x00000002

MajorVersion = 1
MinorVersion = 1

Off = 0
On = 1
Cycle = 2
Disabled = 3

Blanked = 0
Internal = 1
External = 2

Notify = 0
NumberEvents = 1

class GetVersion(rq.ReplyRequest):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(0),
            rq.RequestLength(),
            rq.Card8('major_version'),
            rq.Card8('minor_version'),
            rq.Pad(2),
            )

    _reply = rq.Struct(
            rq.Pad(1), # type
            rq.Pad(1),
            rq.Card16('sequence_number'),
            rq.Pad(4), # length
            rq.Card16('major_version'),
            rq.Card16('minor_version'),
            rq.Pad(20),
            )

def get_extension_major(dpy):
    try:
        return dpy.display.get_extension_major(extname)
    except KeyError:
        info = dpy.query_extension(extname)
        dpy.display.set_extension_major(extname, info.major_opcode)
        return info.major_opcode


def get_version(dpy, major=MajorVersion, minor=MinorVersion):
    return GetVersion(
            display=dpy.display,
            opcode=get_extension_major(dpy),
            major_version=major,
            minor_version=minor)

class QueryInfo(rq.ReplyRequest):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(1),
            rq.RequestLength(),
            rq.Drawable("drawable"),
            )

    _reply = rq.Struct(
            rq.Pad(1), # type
            rq.Card8('state'), # FIXME: BYTE?
            rq.Card16('sequence_number'),
            rq.Pad(4), # length
            rq.Window('window'),
            rq.Card32('til_or_since'),
            rq.Card32('idle'),
            rq.Card32('event_mask'),
            rq.Card8('kind'), # FIXME: BYTE?
            rq.Pad(7),
            )

def query_info(dpy, drawable):
    return QueryInfo(
            display=dpy.display,
            opcode=get_extension_major(dpy),
            drawable=drawable)
