This web app generates full-history ([RFC5005][]) RSS feeds for web
sites that have consistent weekly update schedules and predictable URLs.
For example, this could work for a hypothetical site that has been
updating every Monday since 2005, and where the URL for each post is
formed using the year, month, and day of that post.

[RFC5005]: https://tools.ietf.org/html/rfc5005

**Try it out at <https://fh.minilop.net/>**

Full-history feeds are not yet supported by any feed reader that I'm
aware of, but at the least, any feed reader should see the most recent
50 posts from feeds generated with this tool. So you might find this
useful for some sites that don't have RSS feeds already, even if you
don't get the benefit of seeing the complete feed history.

## Things this is not

This is not a web crawler. It assumes that you've provided correct start
date and update time settings, and generates a feed containing all posts
between that start date and today. If the settings are wrong, the feed
will blithely link to pages that don't exist.

Because there are very few configuration settings, all feed
configuration is stored in the feed URL itself, so this app does not use
a database. Any archived feed can be quickly generated from these
parameters with just a little bit of date math.

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
