from flask import Blueprint, render_template, abort, redirect, url_for
from app.models import Event, BlogPost
from datetime import datetime, date, timedelta

client = Blueprint('client', __name__)

@client.route('/')
def index():
    events = Event.objects(end_date__gt=datetime.now()).order_by('start_date')[:4]
    blog_post = BlogPost.objects(published=True).order_by('-date_published')[0]
    return render_template('index.html', events=events, blog_post=blog_post)

@client.route('/contact')
def contact():
    return render_template('contact.html')

@client.route('/events')
def events():
    today = date.today()
    last_sunday = datetime.combine(today - timedelta(days=today.isoweekday()+7),
                                   datetime.min.time())
    next_sunday = datetime.combine(today + timedelta(days=7-today.isoweekday()),
                                   datetime.min.time())
    recent_and_upcoming = Event.objects(start_date__gt=last_sunday).order_by('start_date-')

    recent_events = recent_and_upcoming.filter(end_date__lt=datetime.now())

    events_this_week = recent_and_upcoming.filter(end_date__gt=datetime.now(),
                                                  start_date__lt=next_sunday)

    upcoming_events = recent_and_upcoming.filter(start_date__gt=next_sunday)[:4]

    return render_template('events/events.html',
                           recent_events=recent_events,
                           events_this_week=events_this_week,
                           upcoming_events=upcoming_events)

@client.route('/events/<int:index>')
def event_archive(index):
    index = int(index)
    if index <= 0:
        return redirect(url_for('.events'))

    today = date.today()
    last_sunday = datetime.combine(today - timedelta(days=today.weekday()+7),
                                   datetime.min.time())

    past_events=Event.objects(start_date__lt=last_sunday).order_by('start_date-')

    if not past_events:
        return redirect(url_for('.events'))

    previous_index = index - 1
    next_index = index + 1 if len(past_events) > 10*index else None
    return render_template('events/archive.html',
                           events=past_events[10*(index-1):10*(index)],
                           previous_index=previous_index,
                           next_index=next_index)

@client.route('/events/<slug>')
def event(slug):
    if Event.objects(slug=slug).count() == 0:
        abort(404) # Either invalid event ID or duplicate IDs.

    event = Event.objects(slug=slug)[0]


    if event.is_recurring:
        upcoming_event_instances = Event.objects(slug=slug, start_date__gte=date.today()).order_by('start_date')
        if upcoming_event_instances:
            event = upcoming_event_instances[0]
        else:
            event = event.parent_series.events[-1]

        upcoming_events = Event.objects(start_date__gte=date.today(),
                                id__ne=event.id).order_by('start_date')[:3]


        return render_template('events/event.html', event=event,
                               upcoming_events=upcoming_events)

    upcoming_events = Event.objects(start_date__gte=date.today(),
                                    id__ne=event.id).order_by('start_date')[:3]

    return render_template('events/event.html', event=event,
                           upcoming_events=upcoming_events)

@client.route('/events/<slug>/<index>')
def recurring_event(slug, index):
    if Event.objects(slug=slug).count() == 0:
        abort(404) # Either invalid event ID or duplicate IDs.

    index = int(index)

    event = Event.objects(slug=slug)[0]

    upcoming_events = Event.objects(start_date__gte=date.today(),
                                id__ne=event.id).order_by('start_date')[:3]


    if not event.is_recurring or not event.parent_series:
        return redirect(url_for('.event', slug=slug))

    if len(event.parent_series.events) <= index:
      abort(404)

    event = event.parent_series.events[index]
    return render_template('events/event.html', event=event,
                           upcoming_events=upcoming_events)
