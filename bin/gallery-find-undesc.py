#!/usr/bin/python
import sys
import os.path

IMAGE_FILETYPES = (".jpg", ".jpeg", ".png")

def walk_callback(arg, dir, names):
  for n in names:
    fn, ext = os.path.splitext(n)
    if not ext.lower() in IMAGE_FILETYPES:
      continue
    fullpath = os.path.join(dir, n)
    descfile = fullpath + ".desc"
    if not os.path.exists(descfile):
      print fullpath

if __name__ == "__main__":
  dirs = ["."]
  if len(sys.argv) > 1:
    dirs = sys.argv[1:]
  for dir in dirs:
    os.path.walk(dir, walk_callback, None)
