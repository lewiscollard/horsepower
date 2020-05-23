#!/usr/bin/env python
import glob
import sys
import os
import os.path

dirname = "."

if len(sys.argv) > 1:
    dirname = sys.argv[1]

driver = input("Driver name: ").strip()
team = input("Team name: ").strip()

if not driver:
    yn = input("no driver name given - carry on? (y/N) ").strip()
    if not yn or not yn[0] == "y":
        sys.exit()

patterns = ["*.jpg", "*.JPG"]

glob_patterns = [os.path.join(dirname, pattern) for pattern in patterns]

files = []

for pattern in glob_patterns:
    files = files + glob.glob(pattern)

for fn in files:
    descfile = "{}.desc".format(fn)
    print("writing {}".format(os.path.abspath(descfile)))
    fd = open(descfile, "wb")
    if driver:
        fd.write("Driver: {}\n".format(driver))
    if team:
        fd.write("Team: {}\n".format(team))
    fd.close()
