#!/usr/bin/env python

import sys, os, curses
import mapper

class GUI(object):
    def __init__(self):
        self.quit = False

    def setMonitor(self, monitor):
        self.mon = monitor

    def main(self, stdscr):
        self.stdscr = stdscr
        height, width = stdscr.getmaxyx()
        curses.curs_set(0)
        stdscr.timeout(0)

        self.devicelistL = listpad(curses.newpad(300, 20))
        self.devicelistR = listpad(curses.newpad(300, 20))

        self.screen = stdscr.subwin(height, width, 0, 0)
        self.screen.box()
        self.screen.hline(2, 1, curses.ACS_HLINE, width-2)

        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_WHITE)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)

        self.devicelistR.cursor_show(False)
        self.cur_list = self.devicelistL

        while not self.quit:
            c = stdscr.getch()
            if   c==curses.KEY_UP:     self.cur_list.cursor_add(-1)
            elif c==curses.KEY_DOWN:   self.cur_list.cursor_add(1)
            elif c==curses.KEY_RIGHT:
                self.cur_list = self.devicelistR
                self.devicelistL.cursor_show(False)
                self.devicelistR.cursor_show(True)
            elif c==curses.KEY_LEFT:
                self.cur_list = self.devicelistL
                self.devicelistL.cursor_show(True)
                self.devicelistR.cursor_show(False)
            elif c==ord('q'):
                break;
            elif c==ord(' '):
                self.cur_list.sel_at_cursor()
            elif c==ord('l'):
                self.mon.link(self.devicelistL.names(),
                              self.devicelistR.names())
            elif c==-1:
                self.mon.poll(30)
                continue

            self.devicelistL.pad.refresh( 0,0, 3,1, 20,75 )
            self.devicelistR.pad.refresh( 0,0, 3,width-21, 20,75 )
            self.screen.refresh()

    def start(self):
        curses.wrapper(self.main)

class listpad(object):
    def __init__(self, pad):
        self.pad = pad
        self.length = 0
        self.curs = 0
        self.sel = []
        self.show_curs = True
        self.assocdata = {}

    def update_data(self, data):
        self.length = 0
        for n, d in enumerate(data):
            self.pad.addstr(n,0, d['name'])
            self.length += 1
            self.assocdata[n] = d

    def cursor_add(self, n):
        prevcurs = self.curs
        self.curs = max(min(self.curs+n, self.length-1), 0)
        if prevcurs in self.sel:
            self.pad.chgat( prevcurs, 0, 20, curses.color_pair(3) )
        else:
            self.pad.chgat( prevcurs, 0, 20, curses.color_pair(1) )
        self.pad.chgat( self.curs, 0, 20, curses.color_pair(2) )

    def cursor_show(self, show):
        self.show_curs = show
        if show:
            self.pad.chgat( self.curs, 0, 20, curses.color_pair(2) )
        else:
            self.pad.chgat( self.curs, 0, 20, curses.color_pair(4) )

    def sel_at_cursor(self):
        if self.curs in self.sel:
            self.sel.remove(self.curs)
        else:
            self.sel.append(self.curs)

    def names(self):
        return [self.assocdata[x]['name'] for x in self.sel]

class mappermonitor(object):
    def __init__(self, gui):
        self.gui = gui
        self.mon = mapper.monitor()
        self.poll = self.mon.poll
        self.mon.db.add_device_callback(self.device_handler)

    def setGUI(self, gui):
        self.gui = gui

    def device_handler(self, record, action):
        self.gui.devicelistL.update_data(self.mon.db.all_devices())
        self.gui.devicelistR.update_data(self.mon.db.all_devices())

    def link(self, devicesL, devicesR):
        [self.mon.link(x, y) for x in devicesL for y in devicesR]

theGUI = GUI()
mon = mappermonitor(theGUI)
theGUI.setMonitor(mon)
theGUI.start()
