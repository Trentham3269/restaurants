#!/usr/bin/python3
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem


app = Flask(__name__)


# Create db session
# https://stackoverflow.com/questions/15140554
engine = create_engine('sqlite:///restaurantmenu.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


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
