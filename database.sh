#!/bin/bash
if [ -e restaurantmenu.db ]
then
    rm -f restaurantmenu.db && python3 database_setup.py && python3 lotsofmenus.py
    echo 'Remove existing/recreate fresh db'
else
    python3 database_setup.py && python3 lotsofmenus.py
    echo 'Recreate fresh db'
fi