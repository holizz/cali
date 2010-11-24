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

import os
import re
import datetime
import curses

class Cali:

    # Signal
    class Quit:
        pass

    class Bounce:
        def __init__(self, stdscr):
            self.stdscr = stdscr

        def __enter__(self):
            self.y, self.x = self.stdscr.getyx()

        def __exit__(self):
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

    def __init__(self):
        self.config = {'dates': None}
        self.today = datetime.date.today()
        self.days = {}
        self.dates = {}

        if self.config['dates']:
            with open(os.path.expanduser(os.path.expandvars(self.config['dates']))) as f:
                for l in f.readlines():
                    line = l.strip()
                    d = re.match('(\d{4})-(\d{2})-(\d{2})', line)
                    if d:
                        date = datetime.date([int(x) for x in d])
                        self.dates.setdefault(date, [])
                        self.dates[date].append(line)

        self.key = {}
        for v,k in self.KEYBINDINGS.items():
            for kk in k:
                self.key[kk] = v

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
                self.move(self.key[self.stdscr.getch])
        except Cali.Quit:
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
                if self.has_items(counter):
                    self.stdscr.attron(curses.A_UNDERLINE)
                if counter == self.today:
                    self.stdscr.attron(curses.A_REVERSE)
                self.stdscr.addstr("%2d" % counter.day)
                if counter == self.today:
                    self.stdscr.attroff(curses.A_REVERSE)
                if self.has_items(counter):
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
                y = self.days[last.day][1]
                for l in self.dates[self.today]:
                    y += 2
                    self.stdscr.move(y,0)
                    self.stdscr.addstr(l)

    def movecursor(self, old):
        if old != self.today:
            a = self.days[old.day]
            if self.has_items(old):
                self.stdscr.attron(curses.A_UNDERLINE)
            self.stdscr.move(a[1], a[0])
            self.stdscr.addstr("%2d" % old.day)
            if self.has_items(old):
                self.stdscr.attroff(curses.A_UNDERLINE)
        if self.has_items(self.today):
            self.stdscr.attron(curses.A_UNDERLINE)
        self.stdscr.attron(curses.A_REVERSE)
        a = self.days[self.today.day]
        self.stdscr.move(a[1], a[0])
        self.stdscr.addstr("%2d" % self.today.day)
        self.stdscr.attroff(curses.A_REVERSE)
        if self.has_items(self.today):
            self.stdscr.attroff(curses.A_UNDERLINE)
        self.stdscr.move(a[1], a[0]+1)

#   def update(&block)
#       oldtoday = @today.dup
#       yield
#       if oldtoday.month == @today.month and oldtoday.year == @today.year
#           movecursor(oldtoday)
#       else
#           displaycal
#       end
#   end

#   def move(to)
#       case to
#       when :quit
#           throw :quit
#       when :refresh
#           displaycal
#       when :tomorrow
#           update { @today += 1 }
#       when :yesterday
#           update { @today -= 1 }
#       when :nextweek
#           update { @today += 7 }
#       when :prevweek
#           update { @today -= 7 }
#       when :nextmonth
#           oldtoday = @today.dup
#           @today += 4*7
#           if @today.month == oldtoday.month
#               @today += 7
#           end
#           displaycal
#       when :prevmonth
#           oldtoday = @today.dup
#           @today -= 4*7
#           if @today.month == oldtoday.month
#               @today -= 7
#           end
#           displaycal
#       when :nextyear
#           oldtoday = @today.dup
#           @today += 52*7
#           while @today.year == oldtoday.year or @today.month != oldtoday.month
#               @today += 7
#           end
#           displaycal
#       when :prevyear
#           oldtoday = @today.dup
#           @today -= 52*7
#           while @today.year == oldtoday.year or @today.month != oldtoday.month
#               @today -= 7
#           end
#           displaycal
#       when :nextevent
#           update { 
#               newtoday = @dates.keys.select{|d| @today < d }.sort.first
#               @today = newtoday if newtoday
#           }
#       when :prevevent
#           update {
#               newtoday = @dates.keys.select{|d| @today > d }.sort.last
#               @today = newtoday if newtoday
#           }
#       end
#       displayevents
#   end

    def weekdays(self):
        wds = []
        counter = self.today - datetime.timedelta(self.today.isoweekday())
        n = 0
        while n < 7:
            #TODO: handle other charsets correctly
            wds.append(counter.strftime('%a')[0])
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

    def has_items(self, date=None):
        if date is None:
            date = self.today
        date in self.dates

Cali().run()
