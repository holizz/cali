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
    class Quit:
        pass

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
        pass
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

#   def displaydays
#       counter = (first - first.wday)
#       before_month = true
#       after_month = false
#       while not after_month
#           if counter.month == @today.month and before_month
#               before_month = false
#           elsif counter.month != @today.month and not before_month
#               after_month = true
#           end
#           if before_month or after_month
#               Ncurses.printw("   ")
#               Ncurses.printw("\n") if after_month
#           else
#               @days[counter.day] = [Ncurses.getcurx(Ncurses.stdscr),
#                   Ncurses.getcury(Ncurses.stdscr)]
#               if counter == @today
#                   x,y = Ncurses.getcurx(Ncurses.stdscr),Ncurses.getcury(Ncurses.stdscr)
#               end
#               Ncurses.attron(Ncurses::A_UNDERLINE) if has_items?(counter)
#               Ncurses.attron(Ncurses::A_REVERSE) if counter == @today
#               Ncurses.printw("%2d" % counter.day)
#               Ncurses.attroff(Ncurses::A_REVERSE) if counter == @today
#               Ncurses.attroff(Ncurses::A_UNDERLINE) if has_items?(counter)
#               Ncurses.printw(" ")
#           end
#           if counter.wday == 6
#               Ncurses.printw("\n")
#           end
#           counter += 1
#       end
#       Ncurses.move(y,x+1)
#   end

#   def displayevents
#       displaycal
#       bounce {
#           y = @days[last.day][1]
#           @dates[@today].each {|l|
#               y += 2
#               Ncurses.move(y,0)
#               Ncurses.printw("#{l}")
#           } if @dates[@today]
#       }
#   end

#   def bounce (&block)
#       y,x = Ncurses.getcury(Ncurses.stdscr),Ncurses.getcurx(Ncurses.stdscr)
#       yield
#       Ncurses.move(y,x)
#   end

#   def movecursor(old)
#       if old != @today
#           a = @days[old.day]
#           Ncurses.attron(Ncurses::A_UNDERLINE) if has_items?(old)
#           Ncurses.mvprintw(a[1],a[0],"%2d" % old.day)
#           Ncurses.attroff(Ncurses::A_UNDERLINE) if has_items?(old)
#       end
#
#       Ncurses.attron(Ncurses::A_UNDERLINE) if has_items?(@today)
#       Ncurses.attron(Ncurses::A_REVERSE)
#       a = @days[@today.day]
#       Ncurses.mvprintw(a[1],a[0],"%2d" % @today.day)
#       Ncurses.attroff(Ncurses::A_REVERSE)
#       Ncurses.attroff(Ncurses::A_UNDERLINE) if has_items?(@today)
#       Ncurses.move(a[1],a[0]+1)
#   end

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

#   def weekdays
#       wds = []
#       counter = (@today - @today.wday)
#       n = 0
#       while n < 7
#           #TODO: handle other charsets correctly
#           wds << counter.strftime('%a')[0..1]
#           counter += 1
#           n += 1
#       end
#       wds
#   end

#   def first
#       Date.new(@today.year,@today.month,1)
#   end

#   def last
#       newlast = @today.dup
#       until newlast.month != @today.month
#           last = newlast.dup
#           newlast += 1
#       end
#       last
#   end

#   def has_items?(date=@today)
#       @dates.include?(date)
#   end
#nd

Cali().run()
