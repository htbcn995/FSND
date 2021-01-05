#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
db.init_app(app)

migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(JSON, nullable=False)
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship("Show", backref="venue", cascade="all, delete-orphan", lazy=True)
    

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(JSON, nullable=False)
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='artist', lazy=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
   

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime
""
#utility function
def num_shows(id, object="venue"):
  if object=="venue":
    shows = Show.query.filter_by(venue_id=id).all()
  else:
    shows = Show.query.filter_by(artist_id=id).all()
  current_time = datetime.now()
  count = 0
  for show in shows:
    if show.start_time > current_time:
      count += 1
    return count


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #        num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  temp_dic = {}
  venues = Venue.query.all()
  for venue in venues:
    venue_dic = {}
    venue_dic['id'] = venue.id
    venue_dic['name'] = venue.name
    venue_dic['num_shows'] = num_shows(venue.id)
    location = (venue.city, venue.state)
    try:
      temp_dic[location].append(venue_dic)
    except:
      temp_dic[location] = [venue_dic]
  for area in temp_dic:
    location_dic = {}
    location_dic['city'] = area[0]
    location_dic['state'] = area[1]
    location_dic['venues'] = temp_dic[area]
    data.append(location_dic)
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  venues = Venue.query.all()
  matches = []
  for venue in venues:
    if search_term.upper() in venue.name.upper():
      match = {
        "id" : venue.id,
        "name" : venue.name,
        "num_upcoming_shows" : num_shows(venue.id)
      }
      matches.append(match)
  
  response = {}
  response["count"] = len(matches)
  response["data"] = matches

  return render_template('pages/search_artists.html', results=response, search_term = search_term)
 
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  data = {
    "id": venue.id,
    "name": venue.name,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "image_link": venue.image_link,
    "facebook_link": venue.facebook_link,
    "genres": venue.genres,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description
    }

  upcoming_shows = []
  past_shows = []
  current_time = datetime.now()
  all_shows = Show.query.filter_by(venue_id = venue.id).all()
  for show in all_shows:
    show_dic = {
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time)
    }
    if show.start_time > current_time:
      upcoming_shows.append(show_dic)
    else:
      past_shows.append(show_dic)
  data["upcoming_shows"] = upcoming_shows
  data["past_shows"] = past_shows
  data["upcoming_shows_count"] = len(upcoming_shows)
  data["past_shows_count"] = len(past_shows)

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm()
  if not form.validate():
    flash('error : ' + str(form.errors))
    return render_template('forms/new_venue.html', form=form)
  else:
    #search duplicate record
    venue = Venue.query.filter_by(name = form.data["name"], phone = form.data["phone"]).first()
    if venue:
      flash("Alredy registered")
      return render_template('forms/new_venue.html', form=form)
    else:
      try:
        form_values = dict(form.data)
        del form_values["csrf_token"]
        venue = Venue(**form_values)
        db.session.add(venue)
        db.session.commit()
        flash(form.data["name"] + ' was successfully listed!')
      except:
        db.session.rollback()
        flash('error : ' + form.data["name"] + 'could not be listed.')
      finally:
        db.session.close()
      return render_template('pages/home.html')

#Delete Venue record
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    flash('Venue was deleted.')
    return jsonify({'succecc': True})

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the databaseat
  artists = Artist.query.all()
  data = []
  for artist in artists:
    data.append({"id": artist.id, "name": artist.name})

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  artists = Artist.query.all()
  matches = []
  for artist in artists:
    if search_term.upper() in artist.name.upper():
      match = {
        "id" : artist.id,
        "name" : artist.name,
        "num_upcoming_shows" : num_shows(artist.id, object="artist")
      }
      matches.append(match)
  
  response = {}
  response["count"] = len(matches)
  response["data"] = matches

  return render_template('pages/search_artists.html', results=response, search_term = search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  artist = Artist.query.get(artist_id)
  data = {
    "id": artist.id,
    "name": artist.name,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "image_link": artist.image_link,
    "genres": artist.genres,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description
  }

  upcoming_shows = []
  past_shows = []
  current_time = datetime.now()
  shows = Show.query.filter_by(artist_id = artist.id).all()
  for show in shows:
    show_dic = {
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime("%d/%m/%Y, %H:%M")
    }
    if show.start_time > current_time:
      upcoming_shows.append(show_dic)
    else:
      past_shows.append(show_dic)

  data["upcoming_shows"] = upcoming_shows
  data["past_shows"] = past_shows
  data["upcoming_shows_count"] = len(upcoming_shows)
  data["past_shows_count"] = len(past_shows)

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm()
  form.name.data = artist.name
  form .city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website.data = artist.website
  form.facebook_link.data = artist.facebook_link
  form.image_link.data = artist.image_link
  form.genres.data = artist.genres

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  if not form.validate():
    flash('ERROR :' + str(form.errors))
    return redirect(url_for('edit_artist_submission', artist_id = artist_id))
     
  else:
    try:
      artist = Artist.query.get(artist_id)
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.genres = form.genres.data
      artist.facebook_link = form.facebook_link.data
      artist.website = form.website.data
      artist.image_link = form.image_link.data
      artist.seeking_venue = form.seeking_venue.data
      artist.seeking_description = form.seeking_description.data
      db.session.commit()
      flash('Artist : ID '+ str(artist_id) + ' was successfully updated.')
    except:
      db.session.rollback()
      flash('Artist : ID' + str(artist_id) + ' could not be updated.' + str(form.errors))
    finally:
      db.session.close()
    
    return redirect(url_for('show_artist', artist_id = artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm()
  form.name.data = venue.name
  form .city.data = venue.city
  form.state.data = venue.state
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.website.data = venue.website
  form.facebook_link.data = venue.facebook_link
  form.image_link.data = venue.image_link
  form.genres.data = venue.genres
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
 
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm()
  if not form.validate():
    flash('ERROR :' + str(form.errors))
    return redirect(url_for('edit_venue_submission', venue_id = venue_id))
 
  else:
    try:
      
      venue = Venue.query.get(venue_id)
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.genres = form.genres.data
      venue.facebook_link = form.facebook_link.data
      venue.website = form.website.data
      venue.image_link = form.image_link.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data
      db.session.commit()
      flash('Venue : ID '+ str(venue_id) + ' was successfully updated.')
    except:
      db.session.rollback()
      flash('Venue : ID' + str(venue_id) + ' could not be updated.')
      print(sys.exc_info())
    finally:
      db.session.close()
    
    return redirect(url_for('show_venue', venue_id = venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  
  form = ArtistForm()
  if not form.validate():
    flash('error : ' + str(form.errors))
    return render_template('forms/new_artist.html', form=form)
  else:
    artist = Artist.query.filter_by(name = form.data["name"], phone = form.data["phone"]).first()
    #search duplicate record
    if artist:
      flash("Alredy registered")
      return render_template('forms/new_artist.html', form=form)
    try:
      form_values = dict(form.data)
      del form_values["csrf_token"]
      artist = Artist(**form_values)
      db.session.add(artist)
      db.session.commit()
      flash(form.data['name'] + ' was successfully listed!')
    except:
      db.session.rollback()
      flash('error : ' + form.data['name'] + ' could not be listed.')
    finally:
      db.session.close()
    return render_template('pages/home.html')

  



#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.all()
  data = []
  for show in shows:
    show_dic = {
      "venue_id" : show.venue_id,
      "venue_name" : show.venue.name,
      "artist_id" : show.artist_id,
      "artist_name" : show.artist.name,
      "artist_image_link" : show.artist.image_link,
      "start_time" : str(show.start_time)
    }
    data.append(show_dic)
  
  return render_template('pages/shows.html', shows = data)
  
@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm()
  if not form.validate():
    flash("error : " + str(form.errors))

    return render_template('forms/new_show.html', form=form)

  else:
    try:
      artist = Artist.query.get(form.data["artist_id"])
      assert len(artist.name) > 0
    except:
      flash("Please enter a valid Artist ID.")
      return render_template('forms/new_show.html', form=form)

    try:
      venue = Venue.query.get(form.data["venue_id"])
      assert len(venue.name) > 0
    except:
      flash("Please enter a valid Venue ID.")
      return render_template('forms/new_show.html', form=form)


    try:
      show = Show(
            artist_id=form.data['artist_id'],
            venue_id=form.data['venue_id'],
            start_time=form.data['start_time']
        )
      db.session.add(show)
      db.session.commit()
      flash('Successfully listed')
    except:
      db.session.rollback()
      flash('ERROR : Show could not be listed')
    finally:
      db.session.close()
      return render_template('pages/home.html')
    

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
