import calendar
from collections import namedtuple
from datetime import datetime, timedelta
from flask import Flask
from flask import abort
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
import itertools
import os
import pytz
from werkzeug.routing import BaseConverter

app = Flask(__name__)


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
    return itertools.islice(generate_dates(start, include_day, forward=True), skip, skip + count)


def recent_dates(start, now, include_day, count):
    day = timedelta(days=1)
    current = datetime.combine(now, start.timetz())
    if current > now:
        current -= day
    return itertools.takewhile(lambda x: x >= start, itertools.islice(generate_dates(current, include_day, forward=False), 0, count))


def count_dates(start, now, include_day):
    per_week = sum(include_day)
    weeks = (start - now).days // 7
    start += timedelta(weeks=weeks)
    partial = len(list(itertools.takewhile(lambda x: x < now, generate_dates(start, include_day, forward=True))))
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
        config = value.start_timestamp * 127
        config += sum(included << day for day, included in enumerate(value.include_day)) - 1
        return "{:x}".format(config)


app.url_map.converters['config'] = ConfigConverter


class TimezoneConverter(BaseConverter):
    def to_python(self, value):
        return pytz.timezone(value.replace('+', '/'))

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
        start = datetime.strptime(start_date + ' ' + update_time, "%Y-%m-%d %H:%M:%S")
        config = Config(
            start_timestamp=int(tz.localize(start).timestamp()),
            include_day=["day{}".format(i) in request.args for i in range(7)],
        )
        if sum(config.include_day):
            return redirect(url_for('feed', tz=tz, config=config, template=template))

    return render_template(
        "edit.html",
        day_names=calendar.day_name,
        git_rev=os.getenv("GIT_REV"),
    )


@app.route("/f/<tz:tz>/<config:config>/<path:template>")
@app.route("/<int:page>/<tz:tz>/<config:config>/<path:template>")
def feed(config, tz, template, page=None):
    start = datetime.fromtimestamp(config.start_timestamp, tz)
    now = datetime.now(start.tzinfo)
    per_page = 50
    last_page = count_dates(start, now, config.include_day) // per_page - 1

    links = []
    if page is None:
        dates = recent_dates(start, now, config.include_day, per_page)
        if last_page >= 0:
            links.append(('prev-archive', last_page))
    elif page <= last_page:
        dates = archived_dates(start, config.include_day, page * per_page, per_page)
        links.append(('current', None))
        if page < last_page:
            links.append(('next-archive', page + 1))
        if page > 0:
            links.append(('prev-archive', page - 1))
    else:
        abort(404)

    day_names = [calendar.day_name[day] for day, included in enumerate(config.include_day) if included]
    days_description = ' and '.join(filter(None, (', '.join(day_names[:-1]), day_names[-1])))

    edit_link = url_for(
        'edit_feed',
        _external=True,
        template=template,
        tzname=tz.zone,
        start_date=start.strftime('%Y-%m-%d'),
        update_time=start.strftime('%H:%M:%S'),
        **{"day{}".format(day): "on" for day, included in enumerate(config.include_day) if included}
    )

    feed = render_template(
        "feed.xml",
        template=template,
        days_description=days_description,
        start=start,
        edit_link=edit_link,
        config=config,
        links=links,
        dates=dates,
    )
    response = make_response(feed)
    response.headers['Content-Type'] = 'application/rss+xml'
    return response
