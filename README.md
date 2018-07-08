This web app generates full-history ([RFC5005][]) RSS feeds for web
sites that have consistent weekly update schedules and predictable URLs.
For example, this could work for a hypothetical site that has been
updating every Monday since 2005, and where the only part of the URL
that changes from one post to the next is the date of that post.

[RFC5005]: https://tools.ietf.org/html/rfc5005

**Try it out at <https://fh.minilop.net/>**

Full-history feeds are not yet supported by any feed reader that I'm
aware of, but at the least, any feed reader should see the most recent
50 posts from feeds generated with this tool. So you might find this
useful for some sites that don't have RSS feeds already, even if you
don't get the benefit of seeing the complete feed history.

## Non-features

This is not a web crawler. It assumes that you've provided correct start
date and update time settings, and generates a feed that contains all
the posts that should have been published between that start date and
today. If the settings are wrong, the feed will blithely link to pages
that don't exist.

## Features

I hope folks find this tool useful for generating feeds for sites they
actually want to read, but it may be most valuable as a source of test
data for RSS client developers. Since the links don't have to refer to
real pages, it's easy to construct as small or as large of a feed as you
want. Here's a [sample feed][], which you can [customize][].

[sample feed]: https://fh.minilop.net/f/UTC/2d2d35b394/http://example.com/%25y%25m%25d
[customize]: https://fh.minilop.net/e/UTC/2d2d35b394/http://example.com/%25y%25m%25d

If there are no more than 50 posts in the feed so far, then this tool
generates a "Complete Feed" as defined in [RFC5005][] section 2.
Otherwise it generates "Archived Feeds" as defined in section 4, with 50
posts per page.

There are very few configuration settings, so all feed configuration is
stored in the feed URL itself. This app does not use a database. Any
archived feed can be quickly generated from these parameters with just a
little bit of date math.

We can compute exactly when a new post will next appear in these feeds,
which allows this app to set unusually aggressive cache-control headers.
If you're developing software that consumes RSS, you can use this
service to check that your caching layer is working. On the flip side,
I've tested the server using [REDbot][], a fantastic tool for making
sure you set your HTTP response headers correctly.

[REDbot]: https://redbot.org/

The generated feeds pass validation by [FEED Validator][], including
some RFC5005-specific checks. If you are developing software that
generates RSS or Atom feeds, I encourage you to run samples of your
output through that tool.

[FEED Validator]: http://www.feedvalidator.org/

## Development

Make sure you have [Python 3][] and [pipenv][] installed.

[Python 3]: http://docs.python-guide.org/en/latest/starting/installation/
[pipenv]: https://docs.pipenv.org/install/

Next, create a dedicated development environment with this project's
dependencies installed in it by running:

```sh
git clone https://github.com/jameysharp/predictable.git
cd predictable
pipenv install
```

Now you can run Flask's development web server in that environment:

```sh
FLASK_ENV=development pipenv run flask run
```

At this point you should be able to visit <http://127.0.0.1:5000/> to
see your local version in action. And if you edit `app.py`, the web
server should automatically reload it.
