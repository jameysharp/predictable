import calendar
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from flask import Flask
from flask import abort
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
import itertools
from werkzeug.routing import BaseConverter

app = Flask(__name__)

def generate_dates(start, include_day, forward):
    if forward:
        jump = timedelta(days=1)
    else:
        jump = timedelta(days=-1)
    while True:
        if include_day[start.weekday()]:
            yield start
        start += jump

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
        include_day = [ bool(days_spec & (1 << i)) for i in range(7) ]
        return Config(start_timestamp=start_spec, include_day=include_day)

    def to_url(self, value):
        config = value.start_timestamp * 127
        config += sum(included << day for day, included in enumerate(value.include_day)) - 1
        return "{:x}".format(config)

app.url_map.converters['config'] = ConfigConverter

@app.route("/")
def edit_feed():
    if 'go' in request.args:
        template = request.args['template']
        start_date = request.args['start_date']
        update_time = request.args['update_time']
        start = datetime.strptime(start_date + ' ' + update_time, "%Y-%m-%d %H:%M:%S")
        config = Config(
            start_timestamp=int(start.replace(tzinfo=timezone.utc).timestamp()),
            include_day=[ "day{}".format(i) in request.args for i in range(7) ],
        )
        if sum(config.include_day):
            return redirect(url_for('feed', config=config, template=template))
    return render_template("edit.html", day_names=calendar.day_name)

@app.route("/f/<config:config>/<path:template>")
@app.route("/<int:page>/<config:config>/<path:template>")
def feed(config, template, page=None):
    start = datetime.fromtimestamp(config.start_timestamp, timezone.utc)
    now = datetime.now(start.tzinfo)
    per_page = 50
    last_page = count_dates(start, now, config.include_day) // per_page - 1

    links = []
    if page is None:
        dates = recent_dates(start, now, config.include_day, per_page)
        prev_page = last_page
    elif page <= last_page:
        dates = archived_dates(start, config.include_day, page * per_page, per_page)
        links.append(('current', url_for('feed', config=config, template=template)))
        prev_page = page - 1
        if page < last_page:
            links.append(('next-archive', url_for('feed', config=config, template=template, page=page + 1)))
    else:
        abort(404)

    if prev_page >= 0:
        links.append(('prev-archive', url_for('feed', config=config, template=template, page=prev_page)))

    day_names = [calendar.day_name[day] for day, included in enumerate(config.include_day) if included]
    days_description = ' and '.join(filter(None, (', '.join(day_names[:-1]), day_names[-1])))

    response = make_response(render_template("feed.xml",
        template=template,
        days_description=days_description,
        start=start,
        links=links,
        dates=dates,
    ))
    response.headers['Content-Type'] = 'application/rss+xml'
    return response
