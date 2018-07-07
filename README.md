This web app generates full-history ([RFC5005][]) RSS feeds for web
sites that have predictable weekly update schedules and predictable
URLs. For example, this could work for a hypothetical site that has been
updating every Monday since 2005, and where the URL for each update is
formed using the year, month, and day of that update.

[RFC5005]: https://tools.ietf.org/html/rfc5005

Full-history feeds are not yet supported by any feed reader that I'm
aware of, but at the least, any feed reader should see the most recent
50 posts from feeds generated with this tool. So you might find this
useful for some sites that don't have RSS feeds already, even if you
don't get the benefit of seeing the complete feed history.

**Try it out at <https://fh.minilop.net/>**

## Things this is not

This is not a web crawler. It assumes that you've provided correct start
date and update time settings, and generates a feed containing all posts
between that start date and today.

Because there are very few configuration settings, all feed
configuration is stored in the feed URL itself, so this app does not use
a database. Any archived feed can be quickly generated from these
parameters with just a little bit of date math.
