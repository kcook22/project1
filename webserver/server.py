#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, url_for, g, redirect, Response, send_file, make_response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app = Flask(__name__, static_folder=static_dir, static_url_path="/static", template_folder=tmpl_dir)


#
# The following uses the sqlite3 database test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@w4111db.eastus.cloudapp.azure.com/username
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@w4111db.eastus.cloudapp.azure.com/ewu2493"
#
DATABASEURI = "postgresql://ksc2138:KEGUFW@w4111db.eastus.cloudapp.azure.com/ksc2138"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
# 
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
# 
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
# 
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
#
# END SQLITE SETUP CODE
#



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT * FROM team")
  teams = []
  for result in cursor:
    teams.append(result['name'].encode('utf-8'))  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(teams = teams)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

@app.route('/teamspage/<team_id>')
def teamspage(team_id):
  
  rosterlink = "/teamspage/" + str(team_id)
  newslink= "/news/" + str(team_id)  
  schedulelink= "/schedule/" + str(team_id)
  cursor1 = g.conn.execute("select * from coach where tid=\'" + str(team_id) + "\'")
  coaches = []
  for coach in cursor1:
    coach_info = []
    coach_info.append([result1[0].encode('utf-8') for result1 in g.conn.execute("select photo from person where uid=\'" + str(coach['uid']) + "\'")])
    coach_info.append([result1[0].encode('utf-8') for result1 in g.conn.execute("select name from person where uid=\'" + str(coach['uid']) + "\'")])
    coaches.append(coach_info)     

  cursor = g.conn.execute("select * from player where tid=\'" + str(team_id) + "\'")
  players = []
  for result in cursor:
    entry = []
    uid = result['uid']
    entry.append([result1[0].encode('utf-8') for result1 in g.conn.execute("select photo from person where uid=\'" + str(uid) + "\'")]) 
    entry.append([result1[0].encode('utf-8') for result1 in g.conn.execute("select name from person where uid=\'" + str(uid) + "\'")])
    entry.append(result['number'])
    entry.append(result['position']) 
    entry.append(result['grad_year'])
    entry.append(result['hometown'])
    players.append(entry)

  context = dict(players=players, team_id=team_id, rosterlink=rosterlink,
                 newslink=newslink, schedulelink=schedulelink, coaches=coaches)

  return render_template('teamspage.html', **context)

@app.route('/news/<team_id>')
def news(team_id): 
  rosterlink = "/teamspage/" + str(team_id)
  newslink= "/news/" + str(team_id)  
  schedulelink= "/schedule/" + str(team_id)
  
  articles = g.conn.execute("Select * from make_news where tid=\'" + str(team_id)+ "\'")
  articles_info = []
  for article in articles:
     article_inf = []
     title = article['title']
     date = article['news_date']
     link = [result[0].encode('utf-8') for result in g.conn.execute("select story from news where title=\'" + title + "\' and news_date=\'" + str(date) + "\'")]
     article_inf.append(title)
     article_inf.append(date)
     article_inf.append(link)
     articles_info.append(article_inf)

  
  
  context = dict(articles_info=articles_info, rosterlink=rosterlink, newslink=newslink,
            schedulelink=schedulelink)

  return render_template("anotherfile.html", **context)

@app.route('/schedule/<team_id>')
def schedule(team_id):
  
  rosterlink = "/teamspage/" + str(team_id)
  newslink= "/news/" + str(team_id)  
  schedulelink= "/schedule/" + str(team_id)
  
  
  events = g.conn.execute("select * from competition where tid=\'" + str(team_id) + "\'")
  
  event_list = []
  for event in events:
    event_info = []
    date = event['event_date']
    event_info.append(date)
    time = event['event_time']
    event_info.append(time)
    opponent = [result1[0].encode('utf-8') for result1 in g.conn.execute("select team_name from opponent where opponentid=\'" + str(event['opponentid']) + "\'")]
    event_info.append(opponent)
    outcome = event['outcome']
    event_info.append(outcome)
    event_list.append(event_info)

    context = dict(event_list=event_list, schedulelink=schedulelink, newslink=newslink,
              rosterlink=rosterlink)
    return render_template("schedule.html", **context)

@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test VALUES (NULL, ?)', name)
  return redirect('/')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT,debug=debug, threaded=threaded)

run()

