#!/usr/bin/python
#
# Copyright (c) 2011 Mark D. Pesce
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# This moudule imports vcards to the Plex
# A debugging utility, but has practical uses for import
#
import sys, os
import plex
import json


# This is broken right now.  Probably don't use it.

# When passed a file descriptor thingy of some sort (such as stdin)
# Read the lines of the file as separate vcards, which get added to the Plex.  We hope.
def vcards2plex(a_file):

  plx = plex.Plex()
  for card in a_file.readlines():
    json_card = json.loads(card)
    print json_card,
    plx.add_from_jcard(json_card)
  plx.close()

# If we are called from the command line (which we will be, if we hit this)
# We want to read vcards in from stdin.
# You might call this from the command line with something like:
# cat input.vcards | python vcard2plex.py
#
if __name__ == "__main__":
  #print 'This is broken right now.'
  the_file = sys.stdin
  vcards2plex(the_file)
