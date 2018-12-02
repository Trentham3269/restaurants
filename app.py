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


app = Flask(__name__)


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
    return 'The current session state is {}'.format(login_session['state'])


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
