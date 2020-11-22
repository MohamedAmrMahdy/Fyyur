#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import load_only
import logging
from logging import Formatter, FileHandler
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

venue_genres = db.Table('venue_genres',
    db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True),
    db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True)
)
artist_genres = db.Table('artist_genres',
    db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True)
)

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))

    genres = db.relationship('Genre', secondary=venue_genres, backref=db.backref('venues'), lazy=True)
    shows = db.relationship('Show', backref='venue', lazy=True)

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))

    genres = db.relationship('Genre', secondary=artist_genres, backref=db.backref('artists'))
    shows = db.relationship('Show', backref='artist', lazy=True)

class Genre(db.Model):
    __tablename__ = 'Genre'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)

    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(str(value))
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

@app.route('/404')
def not_found():
  return render_template('errors/404.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  venues = Venue.query.all()
  locations = set()

  for venue in venues:
    locations.add((venue.city, venue.state))

  locations = set(locations)

  for location in locations:
    location_venues = []

    for venue in venues:
      if (venue.city == location[0]) and (venue.state == location[1]):
        shows = Show.query.filter_by(venue_id=venue.id).all()
        num_upcoming_shows = 0

        for show in shows:
          if show.start_time > datetime.now():
            num_upcoming_shows += 1

        location_venues.append({"id": venue.id, "name": venue.name, "num_upcoming_shows": num_upcoming_shows})
    data.append({"city": location[0], "state": location[1], "venues": location_venues})

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  data = []
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()
  for venue in venues:
    shows = Show.query.filter_by(venue_id=venue.id).all()
    num_upcoming_shows = 0

    for show in shows:
      if show.start_time > datetime.now():
        num_upcoming_shows += 1

    data.append({"id": venue.id, "name": venue.name, "num_upcoming_shows": num_upcoming_shows})

  response={
    "count": len(data),
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  if not venue:
    return redirect(url_for('not_found'))

  genres = []
  past_shows = []
  upcoming_shows = []

  for genre in venue.genres:
    genres.append(genre.name)

  for show in venue.shows:
    if show.start_time > datetime.now():
      upcoming_shows.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": format_datetime(show.start_time)
      })
    else:
      past_shows.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": format_datetime(show.start_time)
      })
  data = {
    "id": venue_id,
    "name": venue.name,
    "genres": genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  error = False
  try:
    venue = Venue(
      name = form.name.data,
      city = form.city.data,
      state = form.state.data,
      address = form.address.data,
      phone = form.phone.data,
      seeking_talent = True if form.seeking_talent.data == 'Yes' else False,
      seeking_description = form.seeking_description.data,
      image_link = form.image_link.data,
      website = form.website.data,
      facebook_link = form.facebook_link.data
    )

    for genre in form.genres.data:
      genre_found = Genre.query.filter_by(name=genre).one_or_none()
      if genre_found:
        venue.genres.append(genre_found)
      else:
        new_genre = Genre(name=genre)
        db.session.add(new_genre)
        venue.genres.append(new_genre)

    db.session.add(venue)
    db.session.commit()
  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    abort(500)
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return redirect(url_for('index'))

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  venue = Venue.query.get(venue_id)
  if not venue:
    return redirect(url_for('not_found'))

  error = False

  try:
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Deleting venue ' + venue.name + ' could not be done.')
    abort(500)
  else:
    flash('Venue ' + venue.name + ' was successfully deleted!')
    return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.options(load_only("id", "name")).all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  data = []
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()

  for artist in artists:
    artist_shows = Show.query.filter_by(artist_id=artist.id).all()
    num_upcoming = 0
    for show in artist_shows:
        if show.start_time > datetime.now():
            num_upcoming += 1

    data.append({
        "id": artist.id,
        "name": artist.name,
        "num_upcoming_shows": num_upcoming
    })
  response={
    "count": 1,
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  if not artist:
    return redirect(url_for('not_found'))

  genres = []
  past_shows = []
  upcoming_shows = []

  for genre in artist.genres:
    genres.append(genre.name)

  for show in artist.shows:
    if show.start_time > datetime.now():
      upcoming_shows.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": format_datetime(show.start_time)
      })
    else:
      past_shows.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": format_datetime(show.start_time)
      })
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  artist = Artist.query.get(artist_id)
  if not artist:
    return redirect(url_for('not_found'))

  form = ArtistForm(obj=artist)
  genres = []

  for genre in artist.genres:
    genres.append(genre.name)

  artist={
    "id": artist.id,
    "name": artist.name,
    "genres": genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  error = False
  artist = Artist.query.get(artist_id)
  if not artist:
    return redirect(url_for('not_found'))
  try:
    artist.name = form.name.data
    artist.genres = []
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.seeking_venue = True if form.seeking_venue.data == 'Yes' else False
    artist.seeking_description = form.seeking_description.data
    artist.website = form.website.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
    for genre in form.genres.data:
      genre_found = Genre.query.filter_by(name=genre).one_or_none()
      if genre_found:
        artist.genres.append(genre_found)
      else:
        new_genre = Genre(name=genre)
        db.session.add(new_genre)
        artist.genres.append(new_genre)
    db.session.commit()
  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + form.name.data + ' could not be updated.')
    abort(500)
  else:
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  venue  = Venue.query.get(venue_id)
  if not venue :
    return redirect(url_for('not_found'))

  form = VenueForm(obj=venue)
  genres = []

  for genre in venue.genres:
    genres.append(genre.name)

  venue={
    "id": venue.id,
    "name": venue.name,
    "genres": genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm()
  error = False
  venue = Venue.query.get(venue_id)
  if not venue:
    return redirect(url_for('not_found'))
  try:
    venue.name = form.name.data
    venue.genres = []
    venue.address = form.address.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.phone = form.phone.data
    venue.seeking_talent = True if form.seeking_talent.data == 'Yes' else False
    venue.seeking_description = form.seeking_description.data
    venue.website = form.website.data
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data

    for genre in form.genres.data:
      genre_found = Genre.query.filter_by(name=genre).one_or_none()
      if genre_found:
        venue.genres.append(genre_found)
      else:
        new_genre = Genre(name=genre)
        db.session.add(new_genre)
        venue.genres.append(new_genre)

    db.session.commit()
  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + form.name.data + ' could not be updated.')
    abort(500)
  else:
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  form = ArtistForm()
  error = False
  try:
    artist = Artist(
      name = form.name.data,
      city = form.city.data,
      state = form.state.data,
      phone = form.phone.data,
      seeking_venue = True if form.seeking_venue.data == 'Yes' else False,
      seeking_description = form.seeking_description.data,
      image_link = form.image_link.data,
      website = form.website.data,
      facebook_link = form.facebook_link.data
    )

    for genre in form.genres.data:
      genre_found = Genre.query.filter_by(name=genre).one_or_none()
      if genre_found:
        artist.genres.append(genre_found)
      else:
        new_genre = Genre(name=genre)
        db.session.add(new_genre)
        artist.genres.append(new_genre)

    db.session.add(artist)
    db.session.commit()
  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    abort(500)
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  data = []
  shows = Show.query.all()

  for show in shows:
    data.append({
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "artist_id": show.artist.id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": format_datetime(show.start_time)
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  form = ShowForm()
  error = False
  try:
    show = Show(
      venue_id = form.venue_id.data,
      artist_id = form.artist_id.data,
      start_time = form.start_time.data
    )
    db.session.add(show)
    db.session.commit()
  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Show could not be listed.')
    abort(500)
  else:
    flash('Show was successfully listed!')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
