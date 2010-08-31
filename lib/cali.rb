#!/usr/bin/env ruby

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

require 'date'
require 'optparse'
require 'ncurses'

class Cali
  KEYBINDINGS = {
    ['q'[0]]=> :quit,
    [12]=> :refresh, # C-l
    ['l'[0], Ncurses::KEY_RIGHT, 6]=> :tomorrow, # C-f
    ['h'[0], Ncurses::KEY_LEFT, 2]=> :yesterday, # C-b
    ['j'[0], Ncurses::KEY_DOWN, 14]=> :nextweek, # C-n
    ['k'[0], Ncurses::KEY_UP, 16]=> :prevweek, # C-p
    ['n'[0], Ncurses::KEY_NPAGE]=> :nextmonth,
    ['p'[0], Ncurses::KEY_PPAGE]=> :prevmonth,
    ['}'[0]]=> :nextyear,
    ['{'[0]]=> :prevyear,
    ['w'[0]]=> :nextevent,
    ['b'[0]]=> :prevevent
  }

  def Cali::run
    options = {}
    OptionParser.new { |opts|
      opts.banner = "Usage: cali [-d FILE]"
      opts.on("-d","--dates FILE","Use FILE for events") {|d|
        options[:dates] = d
      }
    }.parse!
    dotcali = Dir["#{ENV['HOME']}/.calirc.rb"][0]
    require dotcali if dotcali
    cali=Cali.new(options[:dates])
    cali.run
  end

  def initialize(dates=nil)
    preinit_hook
    @today = Date.today
    @days = {}
    dates ||= @default_dates
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
    @key = {}
    KEYBINDINGS.each {|k,v|
      k.each {|kk|
        @key[kk] = v
      }
    }
    postinit_hook
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
    displayevents
    catch :quit do
      while true
        move @key[Ncurses.getch]
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
    when :quit
      throw :quit
    when :refresh
      displaycal
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
    displayevents
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
  def preinit_hook
  end
  def postinit_hook
  end
end