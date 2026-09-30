#!/usr/bin/env python3
"""Raise Isaac Sim / Kit windows on DISPLAY (default :1). Polls until timeout."""

from __future__ import annotations

import ctypes
import os
import re
import subprocess
import sys
import time

os.environ.setdefault("DISPLAY", ":1")

libX11 = ctypes.cdll.LoadLibrary("libX11.so.6")
libX11.XOpenDisplay.restype = ctypes.c_void_p
libX11.XOpenDisplay.argtypes = [ctypes.c_char_p]
libX11.XDefaultRootWindow.restype = ctypes.c_ulong
libX11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
libX11.XInternAtom.restype = ctypes.c_ulong
libX11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
libX11.XRaiseWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
libX11.XMapRaised.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
libX11.XSetInputFocus.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
libX11.XFlush.argtypes = [ctypes.c_void_p]
libX11.XSendEvent.argtypes = [
    ctypes.c_void_p,
    ctypes.c_ulong,
    ctypes.c_int,
    ctypes.c_long,
    ctypes.c_void_p,
]


class XClientMessageEvent(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("serial", ctypes.c_ulong),
        ("send_event", ctypes.c_int),
        ("display", ctypes.c_void_p),
        ("window", ctypes.c_ulong),
        ("message_type", ctypes.c_ulong),
        ("format", ctypes.c_int),
        ("data", ctypes.c_long * 5),
    ]


NEEDLE = re.compile(r"isaac|omniverse|kit", re.I)
WIN_RE = re.compile(r"^\s+(0x[0-9a-f]+)\s+\"([^\"]*)\"", re.I)


def window_ids() -> list[int]:
    out = subprocess.check_output(["xwininfo", "-root", "-tree"], text=True, errors="replace")
    found: list[int] = []
    for line in out.splitlines():
        m = WIN_RE.match(line)
        if not m:
            continue
        name = m.group(2)
        if NEEDLE.search(name) and "kit/logs" not in name.lower():
            found.append(int(m.group(1), 16))
    return found


def raise_window(dpy, wid: int) -> None:
    root = libX11.XDefaultRootWindow(dpy)
    libX11.XMapRaised(dpy, wid)
    libX11.XRaiseWindow(dpy, wid)
    atom = libX11.XInternAtom(dpy, b"_NET_ACTIVE_WINDOW", 0)
    ev = XClientMessageEvent()
    ev.type = 33  # ClientMessage
    ev.window = wid
    ev.message_type = atom
    ev.format = 32
    ev.data[0] = 2
    ev.data[1] = 0
    ev.data[2] = 0
    mask = 1 << 20 | 1 << 19  # SubstructureRedirect | SubstructureNotify
    libX11.XSendEvent(dpy, root, 0, mask, ctypes.byref(ev))
    libX11.XSetInputFocus(dpy, wid, 1, 0)  # RevertToParent
    libX11.XFlush(dpy)


def main() -> int:
    timeout_s = float(sys.argv[1]) if len(sys.argv) > 1 else 180.0
    dpy = libX11.XOpenDisplay(None)
    if not dpy:
        print("raise_isaac_window: cannot open DISPLAY", os.environ.get("DISPLAY"), flush=True)
        return 1
    deadline = time.time() + timeout_s
    raised: set[int] = set()
    while time.time() < deadline:
        for wid in window_ids():
            if wid in raised:
                raise_window(dpy, wid)
                continue
            raise_window(dpy, wid)
            raised.add(wid)
            print(f"raise_isaac_window: raised 0x{wid:x}", flush=True)
            try:
                subprocess.run(
                    [
                        "notify-send",
                        "-u",
                        "critical",
                        "Isaac 仿真窗口已打开",
                        "请看桌面 / Alt+Tab 切到 Isaac Sim",
                    ],
                    check=False,
                )
            except OSError:
                pass
        time.sleep(1.0)
    return 0 if raised else 2


if __name__ == "__main__":
    raise SystemExit(main())
