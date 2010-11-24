#!/usr/bin/env python
# encoding: utf-8

# Copyright © 2008-2010, Tom Adams
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

import curses
import datetime
import os
import re

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

def update(fn):
    def a(self):
        oldtoday = self.cali.today
        fn(self)
        if oldtoday.month == self.cali.today.month and oldtoday.year == self.cali.today.year:
            self.cali.movecursor(oldtoday)
        else:
            self.cali.displaycal()
    return a

class Cali:

    # Signal
    class Quit(BaseException):
        pass

    class Bounce:
        def __init__(self, stdscr):
            self.stdscr = stdscr

        def __enter__(self):
            self.y, self.x = self.stdscr.getyx()

        def __exit__(self, cls, value, traceback):
            self.stdscr.move(self.y, self.x)

    KEYBINDINGS = {
            'quit': set([ord('q')]),
            'refresh': set([12]), # C-l
            'tomorrow': set([ord('l'), curses.KEY_RIGHT, 6]), # C-f
            'yesterday': set([ord('h'), curses.KEY_LEFT, 2]), # C-b
            'nextweek': set([ord('j'), curses.KEY_DOWN, 14]), # C-n
            'prevweek': set([ord('k'), curses.KEY_UP, 16]), # C-p
            'nextmonth': set([ord('n'), curses.KEY_NPAGE]),
            'prevmonth': set([ord('p'), curses.KEY_PPAGE]),
            'nextyear': set([ord('}')]),
            'prevyear': set([ord('{')]),
            'nextevent': set([ord('w')]),
            'prevevent': set([ord('b')])
            }

    CONFIG_FILE = '$XDG_CONFIG_HOME/cali/config'

    def __init__(self):
        self.config = {'dates': None}
        self.load_config()
        self.today = datetime.date.today()
        self.days = {}
        self.dates = {}

        if self.config['dates']:
            with open(self.expandpath(self.config['dates'])) as f:
                for l in f.readlines():
                    line = l.strip()
                    d = re.match('(\d{4})-(\d{2})-(\d{2})', line)
                    if d:
                        date = datetime.date(*[int(x) for x in d.groups()])
                        self.dates.setdefault(date, [])
                        self.dates[date].append(line)

        self.key = {}
        for v,k in self.KEYBINDINGS.items():
            for kk in k:
                self.key[kk] = v

    def load_config(self):
        if os.path.exists(self.expandpath(self.CONFIG_FILE)):
            cfg = configparser.ConfigParser()
            cfg.read(self.expandpath(self.CONFIG_FILE))
            self.config.update(cfg.defaults())

    def expandpath(self, p):
        if 'XDG_CONFIG_HOME' not in os.environ:
            os.environ['XDG_CONFIG_HOME'] = '~/.config'
        return os.path.expanduser(os.path.expandvars(p))

    def run(self):
        try:
            self.stdscr = curses.initscr()
            curses.cbreak()
            curses.noecho()
            self.stdscr.keypad(1)
            self.mainloop()
        finally:
            curses.nocbreak()
            self.stdscr.keypad(0)
            curses.echo()
            curses.endwin()

    def mainloop(self):
        self.displaycal()
        self.displayevents()
        try:
            while True:
                c = self.stdscr.getch()
                if c in self.key:
                    self.move(self.key[c])
        except self.Quit:
            pass

    def displaycal(self):
        self.stdscr.clear()
        self.stdscr.move(0,0)
        self.stdscr.addstr(self.today.strftime("   %B %Y\n"))
        
        self.stdscr.addstr(" ".join(self.weekdays())+"\n")
        self.displaydays()
        self.stdscr.refresh()

    def displaydays(self):
        counter = self.first() - datetime.timedelta(self.first().isoweekday())
        before_month = True
        after_month = False
        while not after_month:
            if counter.month == self.today.month and before_month:
                before_month = False
            elif counter.month != self.today.month and not before_month:
                after_month = True
            if before_month or after_month:
                self.stdscr.addstr("   ")
                if after_month:
                    self.stdscr.addstr("\n")
            else:
                self.days[counter.day] = self.stdscr.getyx()
                if counter == self.today:
                    y,x = self.stdscr.getyx()
                if counter in self.dates:
                    self.stdscr.attron(curses.A_UNDERLINE)
                if counter == self.today:
                    self.stdscr.attron(curses.A_REVERSE)
                self.stdscr.addstr("%2d" % counter.day)
                if counter == self.today:
                    self.stdscr.attroff(curses.A_REVERSE)
                if counter in self.dates:
                    self.stdscr.attroff(curses.A_UNDERLINE)
                self.stdscr.addstr(" ")
            if counter.isoweekday() == 6:
                self.stdscr.addstr("\n")
            counter += datetime.timedelta(1)
        self.stdscr.move(y,x+1)

    def displayevents(self):
        self.displaycal()
        if self.today in self.dates:
            with self.Bounce(self.stdscr):
                y = self.days[self.last().day][0]
                for l in self.dates[self.today]:
                    y += 2
                    self.stdscr.move(y,0)
                    self.stdscr.addstr(l)

    def movecursor(self, old):
        if old != self.today:
            a = self.days[old.day]
            if old in self.dates:
                self.stdscr.attron(curses.A_UNDERLINE)
            self.stdscr.move(a[1], a[0])
            self.stdscr.addstr("%2d" % old.day)
            if old in self.dates:
                self.stdscr.attroff(curses.A_UNDERLINE)
        if self.today in self.dates:
            self.stdscr.attron(curses.A_UNDERLINE)
        self.stdscr.attron(curses.A_REVERSE)
        a = self.days[self.today.day]
        self.stdscr.move(a[1], a[0])
        self.stdscr.addstr("%2d" % self.today.day)
        self.stdscr.attroff(curses.A_REVERSE)
        if self.today in self.dates:
            self.stdscr.attroff(curses.A_UNDERLINE)
        self.stdscr.move(a[1], a[0]+1)

    class Actions(object): # new-style class for 2.x
        def __init__(self, cali):
            self.cali = cali
        def quit(self):
            raise Cali.Quit
        def refresh(self):
            self.cali.displaycal()
        @update
        def tomorrow(self):
            self.cali.today += datetime.timedelta(1)
        @update
        def yesterday(self):
            self.cali.today -= datetime.timedelta(1)
        @update
        def nextweek(self):
            self.cali.today += datetime.timedelta(7)
        @update
        def prevweek(self):
            self.cali.today -= datetime.timedelta(7)
        @update
        def nextmonth(self):
            oldtoday = self.cali.today
            self.cali.today += datetime.timedelta(4*7)
            if self.cali.today.month == oldtoday.month:
                self.cali.today += datetime.timedelta(7)
        @update
        def prevmonth(self):
            oldtoday = self.cali.today
            self.cali.today -= datetime.timedelta(4*7)
            if self.cali.today.month == oldtoday.month:
                self.cali.today -= datetime.timedelta(7)
        @update
        def nextyear(self):
            oldtoday = self.cali.today
            self.cali.today += datetime.timedelta(52*7)
            while self.cali.today.year == oldtoday.year or self.cali.today.month != oldtoday.month:
                self.cali.today += datetime.timedelta(7)
        @update
        def prevyear(self):
            oldtoday = self.cali.today
            self.cali.today -= datetime.timedelta(52*7)
            while self.cali.today.year == oldtoday.year or self.cali.today.month != oldtoday.month:
                self.cali.today -= datetime.timedelta(7)
        @update
        def nextevent(self):
            for d in sorted(self.cali.dates.keys()):
                if d > self.cali.today:
                    self.cali.today = d
                    break
        @update
        def prevevent(self):
            for d in reversed(sorted(self.cali.dates.keys())):
                if d < self.cali.today:
                    self.cali.today = d
                    break

    def move(self, to):
        self.Actions(self).__getattribute__(to)()
        self.displayevents()

    def weekdays(self):
        wds = []
        counter = self.today - datetime.timedelta(self.today.isoweekday())
        n = 0
        while n < 7:
            #TODO: handle widechars correctly
            wds.append(counter.strftime('%a')[0:2])
            counter += datetime.timedelta(1)
            n += 1
        return wds

    def first(self):
        return datetime.date(self.today.year, self.today.month, 1)

    def last(self):
        newlast = self.today
        while newlast.month == self.today.month:
            last = newlast
            newlast += datetime.timedelta(1)
        return last

Cali().run()
