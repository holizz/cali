#!/usr/bin/env ruby

# Copyright (c) 2008, Tom Adams
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

require 'date'
require 'optparse'
require 'ncurses'

class Cali
  def initialize(dates=nil)
    @today = Date.today
    @days = {}
    @dates = {}
    if dates
      open(dates){|f|
        until f.eof
          line = f.readline.strip
          d = line.match(/(\d{4})-(\d{2})-(\d{2})/)
          if d
            date = Date.new(*d[1..3].map{|m|m.to_i})
            @dates[date] ||= []
            @dates[date] << line
          end
        end
      }
    end
  end
  def run
    begin
      Ncurses.initscr
      Ncurses.cbreak
      Ncurses.noecho
      Ncurses.keypad(Ncurses.stdscr,true)
      mainloop
    ensure
      Ncurses.endwin
    end
  end
  def mainloop
    displaycal
    while true
      case Ncurses.getch
      when 'q'[0]
        break
      when 12 # C-l
        displaycal
      when 'e'[0], 10 # <RET>
        displayevents
      when 'l'[0], Ncurses::KEY_RIGHT, 6 # C-f
        move :tomorrow
      when 'h'[0], Ncurses::KEY_LEFT, 2 # C-b
        move :yesterday
      when 'j'[0], Ncurses::KEY_DOWN, 14 # C-n
        move :nextweek
      when 'k'[0], Ncurses::KEY_UP, 16 # C-p
        move :prevweek
      when 'n'[0], Ncurses::KEY_NPAGE
        move :nextmonth
      when 'p'[0], Ncurses::KEY_PPAGE
        move :prevmonth
      when '}'[0]
        move :nextyear
      when '{'[0]
        move :prevyear
      when 'w'[0]
        move :nextevent
      when 'b'[0]
        move :prevevent
      end
    end
  end
  def displaycal
    Ncurses.clear
    Ncurses.move(0,0)
    Ncurses.printw(@today.strftime("   %B %Y\n"))
    Ncurses.printw(weekdays.join(" ")+"\n")
    displaydays
    Ncurses.refresh
  end
  def displaydays
    counter = (first - first.wday)
    before_month = true
    after_month = false
    while not after_month
      if counter.month == @today.month and before_month
        before_month = false
      elsif counter.month != @today.month and not before_month
        after_month = true
      end
      if before_month or after_month
        Ncurses.printw("   ")
        Ncurses.printw("\n") if after_month
      else
        @days[counter.day] = [Ncurses.getcurx(Ncurses.stdscr),
                              Ncurses.getcury(Ncurses.stdscr)]
        if counter == @today
          x,y = Ncurses.getcurx(Ncurses.stdscr),Ncurses.getcury(Ncurses.stdscr)
        end
        Ncurses.attron(Ncurses::A_UNDERLINE) if has_items?(counter)
        Ncurses.attron(Ncurses::A_REVERSE) if counter == @today
        Ncurses.printw("%2d" % counter.day)
        Ncurses.attroff(Ncurses::A_REVERSE) if counter == @today
        Ncurses.attroff(Ncurses::A_UNDERLINE) if has_items?(counter)
        Ncurses.printw(" ")
      end
      if counter.wday == 6
        Ncurses.printw("\n")
      end
      counter += 1
    end
    Ncurses.move(y,x+1)
  end
  def displayevents
    displaycal
    bounce {
      y = @days[last.day][1]
      @dates[@today].each {|l|
        y += 2
        Ncurses.move(y,0)
        Ncurses.printw("#{l}")
      } if @dates[@today]
    }
  end
  def bounce (&block)
    y,x = Ncurses.getcury(Ncurses.stdscr),Ncurses.getcurx(Ncurses.stdscr)
    yield
    Ncurses.move(y,x)
  end
  def movecursor(old)
    if old != @today
      a = @days[old.day]
      Ncurses.attron(Ncurses::A_UNDERLINE) if has_items?(old)
      Ncurses.mvprintw(a[1],a[0],"%2d" % old.day)
      Ncurses.attroff(Ncurses::A_UNDERLINE) if has_items?(old)
    end

    Ncurses.attron(Ncurses::A_UNDERLINE) if has_items?(@today)
    Ncurses.attron(Ncurses::A_REVERSE)
    a = @days[@today.day]
    Ncurses.mvprintw(a[1],a[0],"%2d" % @today.day)
    Ncurses.attroff(Ncurses::A_REVERSE)
    Ncurses.attroff(Ncurses::A_UNDERLINE) if has_items?(@today)
    Ncurses.move(a[1],a[0]+1)
  end
  def update(&block)
    oldtoday = @today.dup
    yield
    if oldtoday.month == @today.month and oldtoday.year == @today.year
      movecursor(oldtoday)
    else
      displaycal
    end
  end
  def move(to)
    case to
    when :tomorrow
      update { @today += 1 }
    when :yesterday
      update { @today -= 1 }
    when :nextweek
      update { @today += 7 }
    when :prevweek
      update { @today -= 7 }
    when :nextmonth
      oldtoday = @today.dup
      @today += 4*7
      if @today.month == oldtoday.month
        @today += 7
      end
      displaycal
    when :prevmonth
      oldtoday = @today.dup
      @today -= 4*7
      if @today.month == oldtoday.month
        @today -= 7
      end
      displaycal
    when :nextyear
      oldtoday = @today.dup
      @today += 52*7
      while @today.year == oldtoday.year or @today.month != oldtoday.month
        @today += 7
      end
      displaycal
    when :prevyear
      oldtoday = @today.dup
      @today -= 52*7
      while @today.year == oldtoday.year or @today.month != oldtoday.month
        @today -= 7
      end
      displaycal
    when :nextevent
      update { 
        newtoday = @dates.keys.select{|d| @today < d }.sort.first
        @today = newtoday if newtoday
      }
    when :prevevent
      update {
        newtoday = @dates.keys.select{|d| @today > d }.sort.last
        @today = newtoday if newtoday
      }
    end
  end
  def weekdays
    wds = []
    counter = (@today - @today.wday)
    n = 0
    while n < 7
      #TODO: handle other charsets correctly
      wds << counter.strftime('%a')[0..1]
      counter += 1
      n += 1
    end
    wds
  end
  def first
    Date.new(@today.year,@today.month,1)
  end
  def last
    newlast = @today.dup
    until newlast.month != @today.month
      last = newlast.dup
      newlast += 1
    end
    last
  end
  def has_items?(date=@today)
    @dates.include?(date)
  end
end

if __FILE__ == $0
  options = {}
  OptionParser.new { |opts|
    opts.banner = "Usage: cali [-d FILE]"
    opts.on("-d","--dates FILE","Use FILE for events") {|d|
      options[:dates] = d
    }
  }.parse!
  cali=Cali.new(options[:dates])
  cali.run
end
