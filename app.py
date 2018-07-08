import calendar
from collections import namedtuple
from datetime import datetime, timedelta
from flask import Flask
from flask import Response
from flask import abort
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
import itertools
import os
import pytz
from werkzeug.http import http_date, is_resource_modified, quote_etag
from werkzeug.routing import BaseConverter, ValidationError

app = Flask(__name__)
if app.debug:
    # During development, dump profiling statistics into profile/, one file per
    # request. Open the generated files with:
    #   python -m pstats profile/<filename>
    from werkzeug.contrib.profiler import ProfilerMiddleware
    os.makedirs("profile", exist_ok=True)
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, profile_dir="profile")


def generate_dates(start, include_day, forward):
    if forward:
        jump = timedelta(days=1)
    else:
        jump = timedelta(days=-1)
    current_date = start.date()
    update_time = start.time()
    tz = start.tzinfo
    while True:
        if include_day[current_date.weekday()]:
            yield tz.localize(datetime.combine(current_date, update_time))
        current_date += jump


def archived_dates(start, include_day, skip, count):
    per_week = sum(include_day)
    skip_weeks, skip = divmod(skip, per_week)
    start += timedelta(weeks=skip_weeks)
    return itertools.islice(
        generate_dates(start, include_day, forward=True),
        skip, skip + count
    )


def recent_dates(start, now, include_day, count):
    day = timedelta(days=1)
    current = datetime.combine(now, start.timetz())
    if current > now:
        current -= day
    next_date = next(generate_dates(current + day, include_day, forward=True))
    return next_date, itertools.takewhile(
        lambda x: x >= start,
        itertools.islice(
            generate_dates(current, include_day, forward=False),
            0, count
        )
    )


def count_dates(start, now, include_day):
    per_week = sum(include_day)
    weeks = (now - start).days // 7
    start += timedelta(weeks=weeks)
    partial = len(
        list(
            itertools.takewhile(
                lambda x: x < now,
                generate_dates(start, include_day, forward=True)
            )
        )
    )
    return weeks * per_week + partial


Config = namedtuple('Config', ['start_timestamp', 'include_day'])


class ConfigConverter(BaseConverter):
    regex = r'[0-9A-Fa-f]+'

    def to_python(self, value):
        config = int(value, 16)
        start_spec, days_spec = divmod(config, 127)
        days_spec += 1
        include_day = [bool(days_spec & (1 << i)) for i in range(7)]
        return Config(start_timestamp=start_spec, include_day=include_day)

    def to_url(self, value):
        days_spec = sum(
            1 << day
            for day, included in enumerate(value.include_day)
            if included
        )
        config = value.start_timestamp * 127 + days_spec - 1
        return "{:x}".format(config)


app.url_map.converters['config'] = ConfigConverter


class TimezoneConverter(BaseConverter):
    def to_python(self, value):
        try:
            return pytz.timezone(value.replace('+', '/'))
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValidationError()

    def to_url(self, value):
        return value.zone.replace('/', '+')


app.url_map.converters['tz'] = TimezoneConverter


@app.route("/")
def edit_feed():
    if 'go' in request.args:
        template = request.args['template']
        start_date = request.args['start_date']
        tz = pytz.timezone(request.args['tzname'])
        update_time = request.args['update_time']
        start = datetime.strptime(
            start_date + ' ' + update_time,
            "%Y-%m-%d %H:%M:%S",
        )
        config = Config(
            start_timestamp=int(tz.localize(start).timestamp()),
            include_day=["day{}".format(i) in request.args for i in range(7)],
        )
        if any(config.include_day):
            feed_url = url_for('feed', tz=tz, config=config, template=template)
            return redirect(feed_url)

    return render_template(
        "edit.html",
        day_names=calendar.day_name,
        git_rev=os.getenv("GIT_REV"),
    )


@app.route("/e/<tz:tz>/<config:config>/<path:template>")
def edit_feed_shorturl(tz, config, template):
    start = datetime.fromtimestamp(config.start_timestamp, tz)
    edit_link = url_for(
        'edit_feed',
        template=template,
        tzname=tz.zone,
        start_date=start.strftime('%Y-%m-%d'),
        update_time=start.strftime('%H:%M:%S'),
        **{
            "day{}".format(day): "on"
            for day, included in enumerate(config.include_day)
            if included
        }
    )
    return redirect(edit_link, 301)


@app.route("/f/<tz:tz>/<config:config>/<path:template>")
@app.route("/<int:page>/<tz:tz>/<config:config>/<path:template>")
def feed(config, tz, template, page=None):
    include_day = config.include_day
    start = datetime.fromtimestamp(config.start_timestamp, tz)
    now = datetime.now(start.tzinfo)

    total_posts = count_dates(start, now, include_day)
    per_page = 50
    last_page = total_posts // per_page - 1

    headers = {
        'Date': http_date(now),
    }

    links = []
    if page is None:
        etag = quote_etag(str(total_posts))
        next_date, dates = recent_dates(start, now, include_day, per_page)
        max_age = int((next_date - now).total_seconds())
        if last_page >= 0:
            links.append(('prev-archive', last_page))
    elif page <= last_page:
        etag = '"0"'
        dates = archived_dates(start, include_day, page * per_page, per_page)
        max_age = 7 * 24 * 60 * 60
        links.append(('current', None))
        if page < last_page:
            links.append(('next-archive', page + 1))
        if page > 0:
            links.append(('prev-archive', page - 1))
    else:
        abort(404)

    headers['Cache-Control'] = "public, max-age={}, immutable".format(max_age)
    headers['Expires'] = http_date(now + timedelta(seconds=max_age))
    headers['ETag'] = etag
    if not is_resource_modified(request.environ, etag):
        return Response(status=304, headers=headers)

    day_names = [
        calendar.day_name[day]
        for day, included in enumerate(include_day)
        if included
    ]
    if len(day_names) > 1:
        days_description = '{} and {}'.format(
            ', '.join(day_names[:-1]),
            day_names[-1],
        )
    else:
        days_description = day_names[0]

    feed = render_template(
        "feed.xml",
        template=template,
        days_description=days_description,
        start=start,
        config=config,
        links=links,
        dates=dates,
    )
    return Response(feed, mimetype='application/rss+xml', headers=headers)
