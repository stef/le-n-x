#!/usr/bin/env python

import sys, difflib

def main():
    fromfile, tofile = sys.argv[1:3] # as specified in the usage string

    # we're passing these as arguments to the diff function
    fromlines = open(fromfile, 'U').readlines()
    tolines = open(tofile, 'U').readlines()

    diff = difflib.HtmlDiff().make_file(fromlines, tolines, fromfile,
                                        tofile)
    # we're using writelines because diff is a generator
    sys.stdout.writelines(diff)

if __name__ == '__main__':
    main()
