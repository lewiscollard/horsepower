# Source code for [Horsepower](https://hp.lewiscollard.com/)

Welcome!

This is the source for the small program that generates the static HTML for my motorsports photography website, [Horsepower](https://hp.lewiscollard.com/). You may be able to make use of it if you are a motorsports photographer with some coding skills, or you might just find the README entertaining, or maybe you just want to see some very strange code (a much smarter fellow developer once used the word "interesting" about this code, which is a _fantastic_ adjective to hear). I'm all in favour of you being here either way!

## Why I wrote this

Because I needed to categorise thousands of photographs and make them into the best drifting photography website on the planet. (The code did some of the work, and I'm a passable photographer, and a gorgeous redesign by the wonderful [Chiara Mensa](http://www.chiaramensa.com) did the rest.) I had a few criteria:

### It must generate static HTML

This means that my publication step is `rsync`. It means my backup process is `rsync`. It means that the process of moving to a new server is `rsync`. It means that I have a much wider choice of web servers for the price of an `apt-get` if nginx ever annoys me.

_"OH COOL ANOTHER STATIC SITE GENERATOR"_ - hey don't leave me! I love you! Stay!

### It must work from simple plain-text description files sitting alongside the original photos

Because this means the data to build my website gets backed up along with my photos, for no added effort.

### Those plain-text description files must be the canonical state of the photo

Specifically, I *don't* want them to be some thing that's shoved into some other database. If I get a catastrophic data loss I want to be able to dig out my backups and regenerate the site exactly as-is.

### It must have unique, persistent URLs for any given photo

That means that [this photo](https://hp.lewiscollard.com/galleries/drivers/joao-matos/0175b6-20160521-run-the-josh-payne-joao-matos-GV6W1774/) must always live at its URL. Even if I edit it, even if I change the filename, and _even if I change the means by which a unique identifier for it is generated_. That sort of thing is trivial for a dynamic site, of course, and somewhat trickier for a static site generator.

### It must support arbitrary, and many, taxonomies

That's not _categories_ - the idea of "category" is a taxonomy. I had to be able to create taxonomies like events, drivers and teams.

### And so

Nothing out there fulfills all of the above criteria. So I wrote this over a few evenings!

## How it works

The gallery has a configuration file. It looks like this (abbreviated):

```
Site name: Horsepower - Motorsports photography by Lewis Collard.
Directories: /data/Horsepower/Images/2016-12-17-ndt/out,
        /data/Horsepower/Images/2016-11-26-swaffham/out,
        /data/Horsepower/Images/2016-11-19-rdc/out,
        /data/Horsepower/Images/2016-11-05-ndt/out,
        /data/Horsepower/Images/2016-10-29-swaffham/out
Output to: /www/horsepower/html/
URL: /
Live URL: https://hp.lewiscollard.com/
Template directory: /www/horsepower/templates
```

Some of this explains itself. Many of these variables are just used in templates. Here, "Directories:" is a list of directories, and assumes that each one will have an `event.desc` file therein, which will tell us some details about the event.

You may like the format of the configuration file. I am very fond of it for simple keys-with-string-value pairs. I've been using it in personal projects for over a decade because it's highly readable. Everything before the first colon on a line is a key name. Everything else is its value. And if a line starts with a tab character, it's treated as a continuation of the previous line. Simples! Go look at the `parse_kvp_file` function in the script to see how easy the code is too. (In this case, `Directories` is treated specially - it splits them by comma and `.strip()`s them to get a directory.

So, an `event.desc` file looks like this, in the same very simple file format:

```
Event: Run The Wall @ Swaffham Raceway, November 2016
Date: 2016-11-26
```

This gives the script the name and date of the event. I use ISO-format dates, partly because I find them aesthetically pleasing, partly because sorting by newest is a simple string sort. (Which is probably why I, as a programmer, find them aesthetically pleasing...)

You may notice that while it can contain multiple events on the same day, it won't allow ordering two things on the same day within those dates. This has not been an issue for me.

So, from there, it will walk the directory, and all its subdirectories, for photos that have a corresponding `.desc` file. If a file is called `DSC_0074.JPG`, it will look for `DSC_0074.JPG.desc`, and use that as its description file. A photo description file looks something like this:

```
Driver: Darren Brown, Ross Barnes, Josh Payne
Team: Team Screamin' Wheels
```

Simple, right? And from there, it builds its view of the site. Drivers, [Darren Brown](https://hp.lewiscollard.com/galleries/drivers/darren-brown/), [Ross Barnes](https://hp.lewiscollard.com/galleries/drivers/ross-barnes/) and [Josh Payne](https://hp.lewiscollard.com/galleries/drivers/josh-payne/). Team name: [Team Screamin' Wheels](https://hp.lewiscollard.com/galleries/teams/team-screamin-wheels/). (It can support multiple team names, just as it supports multiple drivers, if comma-separated)

But how does it generate a? Simple, the driver taxonomy lives at `/galleries/drivers`. It generates a slug from the driver name.

How does this stay persistent, even through photo edits? Well, it generates a unique identifier for the photo, consisting of a hash of a bunch of information about the photo, the date, the slug of the event, and the filename. This is unique enough. In the case of this photo, the identifier was `ec1fd0-20161015-norfolk-arena-darren-brown-ross-barnes-DSC_0400`. And so, and _only_ if the description file does not have an identifier, it _writes that back to the description file_. So the one above will look like this:

```
Driver: Darren Brown, Ross Barnes
Team: Team Screamin' Wheels
Identifier: ec1fd0-20161015-norfolk-arena-darren-brown-ross-barnes-DSC_0400
```

This means that if I edit the photo, or even change the method by which I write description files, the identifier will stay the same forever! (I actually did change the identifier description algorithm, and current-me was thankful for that idea by past-me.)

## Things it does badly

### Driver naming

When it reads a description file for a photo and sees:

```
Driver: Chloe Saunders
```

...it will look for a driver gallery that has the name 'Chloe Saunders', create it if there is none, then add the photo to it.

So, it turns out that serialising a human being to a short ASCII text string is a lossy compression method.

Points to you if you spotted it already: the biggest and silliest mistake I made here is that _it assumes driver names are unique_. Yes, _I actually didn't think about this at all as I was writing it_, though in retrospect I'd have probably declared the risk of a name collision minimal and made the same mistake anyway.

Surprise, that broke down when I realised we had two drivers called Ben Cook. I temporarily hacked around it by calling one of them "Ben Cook (2)". (I was handed a reprieve by the fact the second Ben Cook had an identical-looking brother, also a driver, with the same car. So I re-filed them under [Joe & Ben Cook](https://hp.lewiscollard.com/galleries/drivers/joe-amp-ben-cook/). Bullet crudely dodged, for now!)

This method also means that people changing their name will cause them to be a different person as far as the code is concerned. Oh well - it just means going back through the archives and renaming them in their description files, and redirecting their old directory.

### The "awesome"/"greatest hits"

Because I over-generalised the code around taxonomies, the "greatest hits" section of my site lives at `/awesome/awesome/`, rather than `/awesome/`. Bummer, but two lots of awesome is better than one right? You can never have too much of a good thing!

## Things to do later

Improve the identifier generating algorithm.

Solve "things it does badly" above.

## Enjoy!

And if you like me, [email me](mailto:lewiscollard@gmail.com)!
