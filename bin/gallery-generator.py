#!/usr/bin/python
import argparse
import copy
import datetime
import hashlib
import htmlentitydefs
import os
import os.path
from pprint import pprint
import re
import shutil
import sys

import EXIF
import Image, ImageOps
from jinja2 import Environment, FileSystemLoader

IMAGE_EXTENSIONS = ("jpg", "jpeg", "jpe", "png")

DEBUG = True

INTERESTING_EXIF_FIELDS = {
  "Image Model": "Camera",
  "EXIF FocalLength": "Focal length",
}


def debug_print(txt):
  if DEBUG:
    stderr_print(txt)

def stderr_print(txt):
  sys.stderr.write("%s: %s\n" % (sys.argv[0], txt))
  sys.stderr.flush()

def parse_kvp_file(fd, dict=False):
  kvp = []
  lcount = 0
  while True:
    lcount += 1
    line = fd.readline()
    if not line:
      break
    if line.startswith(" ") or line.startswith("\t"):
      # Line continuation
      if not len(kvp):
        stderr_print("warning: line continuation on first line of file")
        continue
      if not line.strip():
        continue
      kvp[-1] = [kvp[-1][0], kvp[-1][1] + " " + line.strip()]
      continue

    line = line.strip()
    if not line:
      # Allow blank lines.
      continue
    lparts = line.split(":", 1)
    if len(lparts) < 2:
      stderr_print("warning: bad line '%s' on line %s of %s" %
      (line, lcount, fd.name))
    k = lparts[0].strip()
    v = lparts[1].strip()
    kvp.append([k, v])
  if dict:
    rv = {}
    for k, v in kvp:
      rv[k] = v
    return rv
  return kvp

def mkdirs(path, silent=True):
  try:
    os.makedirs(path)
  except OSError, detail:
    # 17 = "already exists". We can ignore it safely.
    # XX: is this portable?
    if not detail.errno == 17 and silent:
      raise detail

def slugify(text):
  # Credit: http://snipplr.com/view/26266/
  ret = ""
  for c in text.lower():
    try:
      ret += htmlentitydefs.codepoint2name[ord(c)]
    except:
      ret += c
  ret = re.sub("([a-zA-Z])(uml|acute|grave|circ|tilde|cedil)", r"\1", ret)
  ret = re.sub("\W", " ", ret)
  ret = re.sub(" +", "-", ret)
  return ret.strip()

def extract_hash(path):
  fd = open(path)
  data = fd.read()
  fd.close()
  # Parsing the object hash from the file with a regex is supposedly
  # bad. HOWEVER, this is only ever created by this script, i.e. it
  # will only break if this program outputs this tag in a malformed
  # way.
  hash_re = re.compile(r'<meta name="object-hash" content="([^"]*)"')
  match = hash_re.search(data)
  if not match:
    return None
  return match.group(1)

def template_safe_config(config):
  rv = {}
  for k in config:
    sk = k.lower()
    sk = sk.replace(" ", "_")
    sk = sk.replace("-", "_")
    rv[sk] = config[k]
  return rv

class ImageSize():
  def __init__(self, size, filename, config):
    self.filename = filename
    self.config = config
    self.size = size
    self.height = None
    self.width = None

  def get_url(self):
    return self.config["URL"] + "images/" +  self.size + "/" + self.filename

  def get_path(self):
    return os.path.join(self.config["Output to"], "images", self.size, self.filename)

  def get_size(self):
    if self.height and self.width:
      return (self.height, self.width)
    im = Image.open(self.get_path())
    return im.size

class GalleryImage():
  def __init__(self, config):
    self.config = config
    self.image_file = ""
    self.sizes = {}
    self.drivers = []
    self.driver_objects = []
    self.event = ""
    self.event_object = None
    self.teams = []
    self.team_objects = []
    self.identifier = ""
    self.exif = {}
    self.featured = False
    self.featured_order = 0
    self.awesome = False
    # For arbitrary key-value pairs for use in templates.
    self.kvp = {}
    self.kvp_raw = []
    self.full_width = None
    self.full_height = None

  def hash(self):
    # MD5 is faster and cryptographic security isn't required. Not sure
    # if this is a pointless optimisation.
    h = hashlib.md5()
    for a in ("drivers", "event", "teams", "identifier", "featured",
      "awesome", "exif", "kvp", "config"):
      h.update(str(getattr(self, a)))
    return h.hexdigest()

  def get_basename(self):
    return self.identifier + os.path.splitext(self.image_file)[1]

  def get_size(self, size):
    return self.sizes[size]

  def aspect_ratio_name(self):
    ratio = float(self.full_width) / float(self.full_height)
    if ratio > 1.3:
      return "wide"
    if ratio < 0.8:
      return "tall"
    return "squareish"

  def aspect_padding_bottom(self):
    return round(float(self.full_height) / float(self.full_width) * 100, 3)

  def get_url(self, base, album_slug):
    return self.config["URL"] + "galleries/" + base + "/" + \
      album_slug + "/" + self.identifier + "/"

  def get_title(self):
    parts = []
    for i in self.drivers + self.teams:
      parts.append(i)
    parts.append(self.event)
    return ", ".join(parts)

  def make_sizes(self, base_dir):
    filename = self.get_basename()
    # Copy the full-res version into the full/ directory if
    # source file is newer than the destination file.
    fullres_dir = os.path.join(base_dir, "full")
    fullres_dest = os.path.join(fullres_dir, filename)
    mkdirs(fullres_dir)

    # if it doesn't exist, copy blindly.
    if not os.path.exists(fullres_dest):
      shutil.copyfile(self.image_file, fullres_dest)
    else:
      # Otherwise, check the mtime of source vs dest. If source
      # is newer, copy it.
      if os.path.getmtime(self.image_file) > os.path.getmtime(fullres_dest):
        shutil.copyfile(self.image_file, fullres_dest)
    # Now generate thumbnails!
    self.sizes["full"] = ImageSize("full", filename, self.config)
    resolutions = (
      ("large", (1200, 900), False),
      ("hd", (1920, 1080), False),
      ("thumb", (300, 200), True),
    )
    im = Image.open(self.image_file)
    (self.full_width, self.full_height) = im.size
    for res in resolutions:
      mkdirs(os.path.join(base_dir, res[0]))
      out_file = os.path.join(base_dir, res[0], filename)
      self.sizes[res[0]] = ImageSize(res[0], filename, self.config)
      # Check mtime; if dest mtime > original image file mtime,
      # skip.
      try:
        if os.path.getmtime(out_file) > os.path.getmtime(self.image_file):
          continue
      except:
        # File doesn't exist. It's ok.
        pass
      # Do we crop?
      if res[2]:
        # Yup. Crop, we don't have to do any of the ugly code below.
        ImageOps.fit(im, res[1], Image.ANTIALIAS).save(out_file)
        continue
      # We have to be a bit trickier. We want to make sure that
      # the given resolution is the LARGEST we go.
      target_width = res[1][0]
      target_height = res[1][1]
      aspect_ratio = float(im.size[0]) / im.size[1]
      aspect_ratio_backwards = float(im.size[1]) / im.size[0]
      # Doing this the least clever way possible.
      thumb_width = target_width
      thumb_height = thumb_width / aspect_ratio
      if thumb_height > target_height:
        thumb_height = target_height
        thumb_width = thumb_height / aspect_ratio_backwards
      thumb_height = int(thumb_height)
      thumb_width = int(thumb_width)
      debug_print("saving %s (%sx%s)" % (out_file, thumb_width, thumb_height))
      im.resize((thumb_width, thumb_height), Image.ANTIALIAS).save(out_file)
    # Make 3:2 crop for featured images on slider on front page.
    # (All of my stuff is 3:2 anyway.)
    if self.kvp.has_key("Featured") and self.kvp["Featured"].lower() in ["yes", "1", "true"]:
      if self.kvp.has_key("Featured order"):
        self.featured_order = int(self.kvp["Featured order"])
      out_file = os.path.join(base_dir, "huge_crop", filename)
      if (not os.path.exists(out_file)) or os.path.getmtime(out_file) < os.path.getmtime(self.image_file):
        mkdirs(os.path.join(base_dir, "huge_crop"))
        ImageOps.fit(im, (1200, 800), Image.ANTIALIAS).save(out_file)
      # Special case here because there's no point generating a huge_crop
      # version for an image that isn't going to go on the front page
      # slider.
      self.sizes["huge_crop"] = ImageSize("huge_crop", filename, self.config)

  def generate_identifier(self):
    # Generates an unique (we hope) identifier for the image.
    slug_parts = []
    # Is this a good idea, using a part of a hash? I think
    # a collision is unlikely, given that it's using
    # several other image properties as well.
    fd = open(self.image_file)
    # Read only the first part for speed. Collisions are still
    # very unlikely if you're not generating them deliberately.
    hash_part = hashlib.sha1(fd.read(1024 * 1024 * 100)).hexdigest()[:6]
    slug_parts.append(hash_part)
    fd.close()
    slug_parts.append(self.date.strftime("%Y%m%d"))
    if self.event:
      slug_parts.append(slugify(" ".join(self.event.split(" ")[0:2])))
    if self.drivers:
      for driver in self.drivers:
        slug_parts.append(slugify(driver))
    filename = os.path.splitext(os.path.basename(self.image_file))[0]
    slug_parts.append(filename)
    res = "-".join(slug_parts)
    self.identifier = res
    self.kvp_raw.append(("Identifier", res))
    # Write back the identifier to the desc file.
    # FIXME: scary
    fd = open(self.image_file + ".desc", "w")
    for i in self.kvp_raw:
      fd.write("%s: %s\n" % (i[0], i[1]))
    fd.close()

  def from_file(self, filename):
    desc_file = filename + ".desc"
    debug_print("processing %s" % desc_file)
    fd = open(desc_file)
    lcount = 0
    self.image_file = filename
    kvp = parse_kvp_file(fd)
    for k, v in kvp:
      self.kvp_raw.append((k, v))
      self.kvp[k] = v
      if k == "Driver":
        parts = v.split(",")
        for p in parts:
          self.drivers.append(p.strip())
      elif k == "Team":
        parts = v.split(",")
        for p in parts:
          p = p.strip()
          if p:
            self.teams.append(p)
      elif k == "Featured":
        self.featured = v.lower() in ("1", "0", "yes", "true")
      elif k == "Identifier":
        self.identifier = v
      elif k == "Awesome":
        self.awesome = v.lower() in ("1", "0", "yes", "true")
      else:
        self.kvp[k] = v
    # Parse EXIF data
    try:
      fd = open(filename)
      exif = EXIF.process_file(fd)
      for k in INTERESTING_EXIF_FIELDS:
        if exif.has_key(k):
          self.exif[INTERESTING_EXIF_FIELDS[k]] = exif[k]
    except:
      # Fail silently. (Probably shouldn't.)
      pass

class AlbumBase():
  def __init__(self, config):
    self.pictures = []
    self.picture_count = 0
    self.config = config
    self.title = ""

  def hash(self):
    h = hashlib.md5()
    h.update(self.title)
    for i in self.pictures:
      h.update(i.hash())
    h.update(str(self.config) + self.title)
    return h.hexdigest()

  def count(self):
    return len(self.pictures)

  def add_image(self, img):
    self.pictures.append(img)
    self.picture_count += 1

  def get_slug(self):
    raise NotImplementedError

  def get_base_slug(self):
    raise NotImplementedError

  def get_template_name(self):
    return "photo.html"

  def get_plural_name(self):
    raise NotImplementedError

  def get_url(self):
    return self.config["URL"] + "galleries/" + self.get_base_slug() + "/" + self.get_slug() + "/"

  def get_sort_attr(self):
    raise NotImplementedError

  def get_sort_reverse(self):
    raise NotImplementedError

  def get_cover(self):
    return self.get_first(1)[0]

  def get_first(self, count):
    sorted = self.get_sorted_pictures()
    return sorted[0:count]

  def get_sorted_pictures(self):
    return sorted(self.pictures, key=lambda x: getattr(x, self.get_sort_attr()),
      reverse=self.get_sort_reverse())

  def output(self, template_env, output_dir, template_dir, base_url,
    sort_attr, reverse, force_overwrite):
    base_fs_path = os.path.join(output_dir, self.get_base_slug())
    gallery_dir = os.path.join(base_fs_path, self.get_slug())
    mkdirs(gallery_dir)
    gallery_url = base_url + self.get_slug() + "/"
    pics_sorted = self.get_sorted_pictures()
    template = template_env.get_template(self.get_template_name())
    count = -1
    for pic in pics_sorted:
      count += 1
      pic.context_url = pic.get_url(self.get_base_slug(), self.get_slug())
      pic_hash = pic.hash() + self.hash()
      pic_dir = os.path.join(gallery_dir, pic.identifier)
      mkdirs(pic_dir)
      html_file = os.path.join(pic_dir, "index.html")
      # Let's see if an update is necessary.
      if not force_overwrite and os.path.exists(html_file):
        # Check the mtime of the template.
        if os.path.getmtime(html_file) > os.path.getmtime(template.filename):
          if extract_hash(html_file) == pic_hash:
            debug_print("%s does not need updating." % html_file)
            continue
      ctx = {
        "photo": pic,
        "object_hash": pic_hash,
        "config": template_safe_config(self.config),
      }
      if count > 0:
        ctx["prev_photo"] = pics_sorted[count - 1]
        ctx["prev_photo"].context_url = ctx["prev_photo"].get_url(self.get_base_slug(), self.get_slug())

      else:
        ctx["prev_photo"] = None
      if not (count + 1) == len(pics_sorted):
        ctx["next_photo"] = pics_sorted[count + 1]
        ctx["next_photo"].context_url = ctx["next_photo"].get_url(self.get_base_slug(), self.get_slug())
      else:
        ctx["next_photo"] = None
      fd = open(html_file, "w")
      fd.write(template.render(ctx))
      fd.close()
    index_file = os.path.join(base_fs_path, self.get_slug(), "index.html")
    ctx = {
      "photos": pics_sorted,
      "album": self,
      "hash": self.hash(),
      "config": template_safe_config(self.config),
    }
    template = template_env.get_template("album.html")
    tstr = template.render(ctx)
    fd = open(index_file, "w")
    fd.write(tstr)
    fd.close()

class EventAlbum(AlbumBase):
  def __init__(self, event_name, config):
    AlbumBase.__init__(self, config)
    self.title = event_name
    self.slug = slugify(event_name)
    self.date = None

  def get_slug(self):
    return self.date.strftime("%Y-%m-%d") + "-" + self.slug

  def get_title(self):
    return "Photos from %s" % self.title

  def get_base_slug(self):
    return "events"

  def get_sort_attr(self):
    return "awesome"

  def get_sort_reverse(self):
    return True

class DriverAlbum(AlbumBase):
  def __init__(self, driver_name, config):
    AlbumBase.__init__(self, config)
    self.title = driver_name
    self.slug = slugify(driver_name)

  def get_base_slug(self):
    return "drivers"

  def get_slug(self):
    return self.slug

  def get_title(self):
    return "Photographs of %s" % self.title

  def get_sort_attr(self):
    return "awesome"

  def get_sort_reverse(self):
    return True

class AwesomeAlbum(AlbumBase):
  def __init__(self, config):
    AlbumBase.__init__(self, config)
    self.title = "Greatest Hits"

  def get_title(self):
    return "Greatest Hits"

  def get_base_slug(self):
    return "awesome"

  def get_slug(self):
    return "awesome"

  def get_sort_attr(self):
    return "awesome"

  def get_sort_reverse(self):
    return True


class TeamAlbum(AlbumBase):
  def __init__(self, team_name, config):
    AlbumBase.__init__(self, config)
    self.title = team_name
    self.slug = slugify(team_name)

  def get_title(self):
    return "Photographs of %s" % self.title

  def get_base_slug(self):
    return "teams"

  def get_slug(self):
    return self.slug

  def get_sort_attr(self):
    return "awesome"

  def get_sort_reverse(self):
    return True

class Gallery():
  def __init__(self, config):
    self.drivers = []
    self.events = []
    self.teams = []
    self.config = config
    self.featured = []
    self.awesome = AwesomeAlbum(config)

  def walk_callback(self, arg, path, names):
    for fn in names:
      ext = os.path.splitext(fn)[1]
      fullpath = os.path.join(path, fn)
      if not ext or ext == ".desc":
        continue
      if fn == "event.desc":
        continue
      # Is it a known image file type?
      ext_bare = ext.replace(".", "")
      if not ext_bare.lower() in IMAGE_EXTENSIONS:
        #  Nope.
        #  stderr_print("warning: unknown file type '%s' (%s)" %
        #  (ext_bare, fullpath))
        continue
      # Check for a .desc file for the image.
      if not os.path.exists(fullpath + ".desc"):
        #stderr_print("warning: %s has no description file" % fullpath)
        continue
      img = GalleryImage(self.config)
      img.from_file(fullpath)
      img.event = arg["name"]
      img.date = arg["date"]
      if not img.identifier:
        img.generate_identifier()

      # Generate thumbnails.
      img.make_sizes(os.path.join(self.config["Output to"], "images"))


      # If there are any drivers set as strings...
      if img.drivers:
        # ...look through the images driver objects to find
        # one with an exact name match.
        for driver in img.drivers:
          if driver == "":
            continue
          driver_target = None
          for i in self.drivers:
            if i.title == driver:
              driver_target = i
              break
          if not driver_target:
            driver_target = DriverAlbum(driver, self.config)
            self.drivers.append(driver_target)
          img.driver_objects.append(driver_target)
          driver_target.add_image(img)
      if img.teams:
        for team in img.teams:
          team_target = None
          for i in self.teams:
            if i.title == team:
              team_target = i
              break
          if not team_target:
            team_target = TeamAlbum(team, self.config)
            self.teams.append(team_target)
          img.team_objects.append(team_target)
          team_target.add_image(img)
      # Now grab the event name, see if we've already created
      # one.
      ename = arg["name"]
      event = None
      for ev in self.events:
        if ev.title == ename:
          event = ev
          break
      if not event:
        event = EventAlbum(ename, self.config)
        event.date = arg["date"]
        self.events.append(event)
      event.add_image(img)
      img.event_object = event
      if img.kvp.has_key("Featured") and img.kvp["Featured"].lower() in ["yes", "1", "true"]:
        self.featured.append(img)
      if img.awesome:
        self.awesome.add_image(img)

  def ingest_directory(self, directory):
    debug_print("ingesting directory %s" % directory)
    # Look for the event description file.
    try:
      infofd = open(os.path.join(directory, "event.desc"))
    except Exception, detail:
      stderr_print("%s has no event.desc (%s)" % (directory, detail))
      return
    kvp = parse_kvp_file(infofd, True)
    infofd.close()
    event_details = {
      "name": kvp["Event"],
      "date": datetime.datetime.strptime(kvp["Date"], "%Y-%m-%d")
    }
    os.path.walk(directory, self.walk_callback, event_details)

  def output(self, force_overwrite):
    base_context = {
      "config": template_safe_config(self.config),
    }
    op = self.config["Output to"]
    template_env = Environment(loader=FileSystemLoader(self.config["Template directory"]))
    # Write out the index files. First, the main event pages.
    events = sorted(self.events, key=lambda x: x.date, reverse=True)
    output_path = os.path.join(op, "galleries")
    base_url = self.config["URL"] + "galleries/"
    for event in self.events:
      event.output(template_env, output_path, self.config["Template directory"],
        base_url, "awesome", True, force_overwrite)
    for driver in self.drivers:
      driver.output(template_env, output_path, self.config["Template directory"],
        base_url, "awesome", True, force_overwrite)

    for team in self.teams:
      team.output(template_env, output_path, self.config["Template directory"],
        base_url, "awesome", True, force_overwrite)

    self.awesome.output(template_env, output_path, self.config["Template directory"],
      base_url, "awesome", True, force_overwrite)

    self.write_index(force_overwrite)

  def write_index(self, force_overwrite):
    output_file = os.path.join(self.config["Output to"], "index.html")
    template_env = Environment(loader=FileSystemLoader(self.config["Template directory"]))
    ctx = {}
    ctx["config"] = template_safe_config(self.config)
    self.featured.sort(key=lambda x: x.featured_order, reverse=True)
    ctx["featured"] = self.featured
    events_sorted = sorted(self.events, key=lambda x: x.date, reverse=True)
    drivers_sorted = sorted(self.drivers, key=lambda x: x.picture_count, reverse=True)
    teams_sorted = sorted(self.teams, key=lambda x: x.picture_count, reverse=True)
    ctx["taxonomies"] = [
      {
        "name": "Events",
        "galleries": events_sorted[0:8],
        "index_url": self.config["URL"] + "galleries/events/",
        "slug": "events",
        "button_text": "More events",
        "greatest_hits": self.awesome,
      },
      {
        "name": "Drivers",
        "galleries": drivers_sorted[0:8],
        "index_url": self.config["URL"] + "galleries/drivers/",
        "slug": "drivers",
        "button_text": "All drivers",
      },
      {
        "name": "Teams",
        "galleries": teams_sorted[0:8],
        "index_url": self.config["URL"] + "galleries/teams/",
        "slug": "teams",
        "button_text": "All teams",
      },
    ]
    ctx["awesome"] = self.awesome
    tmpl = template_env.get_template("main-page.html")
    fd = open(output_file, "w")
    fd.write(tmpl.render(ctx))
    fd.close()

    # Write drivers index.
    ctx = {}
    tmpl = template_env.get_template("list-albums.html")
    for title, slug, objects in (
      ("Drivers", "drivers", drivers_sorted),
      ("Events", "events", events_sorted),
      ("Teams", "teams", teams_sorted)
    ):
      ctx = {
        "config": self.config,
        "title": title,
        "slug": slug,
        "base_slug": slug,
        "albums": objects,
      }
      output_dir = os.path.join(self.config["Output to"], "galleries", slug)
      mkdirs(output_dir, False)
      output_file = os.path.join(output_dir, "index.html")
      fd = open(output_file, "w")
      fd.write(tmpl.render(ctx))
      fd.close()

class Page:
  def __init__(self, template, config):
    self.template = template
    self.config = config

  def writeout(self, force_overwrite=False):
    template_env = Environment(loader=FileSystemLoader(self.config["Template directory"]))
    # Calculate the relative path. If our template path is
    # "TEMPLATE_DIR/pages/something/index.html", then we want to write
    # to OUTPUT_DIRECTORY/something/index.html.
    tp = os.path.join(self.config["Template directory"], "pages")
    path_sub = self.template[len(tp):]
    if path_sub.startswith("/"):
      # isn't this always true?
      path_sub = path_sub[1:]
    target = os.path.join(self.config["Output to"], path_sub)
    dir = os.path.dirname(target)
    mkdirs(dir)
    if os.path.exists(target):
      # Check mtime of template vs output file and only overwrite if the
      # source file has been modified. (But if force_overwrite is set to
      # true, overwrite anyway.
      if not os.path.getmtime(self.template) > os.path.getmtime(target):
        if not force_overwrite:
          debug_print("%s: not modified, skipping" % self.template)
          return
    tmpl = template_env.get_template("pages/" + path_sub)
    context = {
      "config": self.config,
    }
    debug_print("writing %s" % target)
    fd = open(target, "w")
    fd.write(tmpl.render(context))
    fd.close()


class PageManager:
  def __init__(self, config):
    self.config = config
    self.pages = []
    self.page_path = os.path.join(self.config["Template directory"], "pages")
    if os.path.exists(self.page_path):
      os.path.walk(self.page_path, self.walk_callback, None)

  def walk_callback(self, arg, path, names):
    for name in names:
      # Check the extension. Ignore anything that is not an HTML
      # file. XXX: good idea?
      ext = os.path.splitext(name)
      if not ext[1].lower() == ".html":
        continue
      fpath = os.path.join(path, name)
      debug_print("adding %s" % fpath)
      page = Page(fpath, self.config)
      self.pages.append(page)

  def writeout(self, force_overwrite=False):
    for i in self.pages:
      i.writeout(force_overwrite)

def main():
  global DEBUG
  ap = argparse.ArgumentParser()
  ap.add_argument(dest="file")
  ap.add_argument("-f", dest="force_overwrite", action="store_true",
    help="regenerate all files whether they have changed or not. Useful "
      "for development where your master files are not changing but "
      "this program is.")
  ap.add_argument("--pages-only", dest="pages_only", action="store_true",
    help="only regenerate pages; don't regenerate albums")
  ap.add_argument("-v", dest="verbose", action="store_true",
    help="be verbose about what we are doing")
  args = ap.parse_args()
  DEBUG=args.verbose
  fd = open(args.file)
  kvp = parse_kvp_file(fd, True)
  if not kvp.has_key("Template directory"):
    kvp["Template directory"] = "./templates"
  if not args.pages_only:
    gallery = Gallery(kvp)
    gallery.output_path = kvp["Output to"]
    for i in kvp["Directories"].split(","):
      i = i.strip()
      gallery.ingest_directory(i)
    gallery.output(args.force_overwrite)
  p = PageManager(kvp)
  p.writeout(args.force_overwrite)

if __name__ == "__main__":
  main()

