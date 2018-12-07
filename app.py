#!/usr/bin/python3
from flask import Flask
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask import session as login_session
import random
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem
import json
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from flask import make_response
import requests


app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu App"


# Create db session
# https://stackoverflow.com/questions/15140554
engine = create_engine('sqlite:///restaurantmenu.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create a state token to prevent request forgery
# Store it in the session for later verification
@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.
                    digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(
            json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorisation code
    code = request.data

    try:
        # Upgrade the authorisation code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorisation code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}'
           .format(access_token))
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1].decode())
    # Abort if there is an error in the access token
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['name'] = data['name']
    login_session['email'] = data['email']

    output = ''
    output += '<h3>Welcome, '
    output += login_session['name']
    output += '!</h3>'
    flash('You are now logged in as {}'.format(login_session['name']))
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/logout/')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is {}'.format(access_token))
    print('User name is: ')
    print(login_session['name'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token={}'.format(
        login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['name']
        response = make_response(json.dumps(
            'Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
@app.route('/restaurants/<int:restaurant_id>/menu/')
def restaurantMenu(restaurant_id):
    # Return the restaurant from the url id
    restaurant = session.query(Restaurant).filter_by(
        id=restaurant_id).one()
    # Return the menu items of the above restaurant
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    # Render html
    return render_template('menu.html',
                           restaurant=restaurant,
                           items=items)


@app.route('/restaurants/<int:restaurant_id>/menu/api/')
def restaurantMenuAPI(restaurant_id):
    # Return the restaurant from the url id
    restaurant = session.query(Restaurant).filter_by(
        id=restaurant_id).one()
    # Return the menu items of the above restaurant
    items = session.query(MenuItem.name, MenuItem.course,
                          MenuItem.description, MenuItem.price).filter_by(
                          restaurant_id=restaurant_id).all()
    # Output as json
    # https://codehandbook.org/working-with-json-in-python-flask/
    item_list = []
    for item in items:
        item_dict = {
            'name': item[0],
            'course': item[1],
            'description': item[2],
            'price': item[3]
        }
        item_list.append(item_dict)
    return jsonify(item_list)


@app.route('/restaurants/<int:restaurant_id>/new/',
           methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    # Restrict new menu item page to logged in users
    if 'name' not in login_session:
        return redirect('/login/')
    if request.method == 'POST':
        new_item = MenuItem(name=request.form['name'],
                            description=request.form['description'],
                            price=request.form['price'],
                            restaurant_id=restaurant_id)
        session.add(new_item)
        session.commit()
        flash('New menu item created!')
        return redirect(url_for('restaurantMenu',
                                restaurant_id=restaurant_id))
    else:
        return render_template('newMenuItem.html',
                               restaurant_id=restaurant_id)


@app.route('/restaurants/<int:restaurant_id>/edit/<int:menu_id>/',
           methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    # Restrict edit menu item page to logged in users
    if 'name' not in login_session:
        return redirect('/login/')
    edit_item = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        if request.form['name']:
            edit_item.name = request.form['name']
        session.add(edit_item)
        session.commit()
        flash('Menu item updated!')
        return redirect(url_for('restaurantMenu',
                                restaurant_id=restaurant_id))
    else:
        return render_template('editMenuItem.html',
                               restaurant_id=restaurant_id,
                               menu_id=menu_id,
                               item=edit_item)


@app.route('/restaurants/<int:restaurant_id>/delete/<int:menu_id>/',
           methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    # Restrict delete menu item page to logged in users
    if 'name' not in login_session:
        return redirect('/login/')
    delete_item = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        session.delete(delete_item)
        session.commit()
        flash('Menu item deleted!')
        return redirect(url_for('restaurantMenu',
                                restaurant_id=restaurant_id))
    else:
        return render_template('deleteMenuItem.html',
                               restaurant_id=restaurant_id,
                               menu_id=menu_id,
                               item=delete_item)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
