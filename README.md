# Books app

Web Programming with Python and JavaScript

## Description:

Beautiful website for rating and review books!

## flask_session

This directory contains the websites current sessions and can safely be deleted when a session is no longer needed.

## Static

###  variables.scss

This file gives the website an awesome look! All style-definitions are contained in this file
Correction: Compiling this file to a variables.css file results to an awesome website!

## Templates:

This file defines the layout/structure of the website.
All other html extend this file!

### Index.html:

The home-page of the website!

### Login.html:

The login-page of the website. When users have registered an account, they can log-in by filling in their credentials.

### Register.html:

Users can register an account on this page, so that they can use their user for logging in.

### Contact.html:

On this page, users can contact the staff of Books B.V.

### Books.html:

Users can search for a book.

### Bookinfo.html:

The page where users will be redirected when clicking on a search-result for a given book

## Application.py

This file contains all the backend logic for the website.
The backend uses the microframework "Flask"

## Books.csv

This file contains all the books that are loaded into the database.

## Import.py

This file contains the scheme and the insert queries for the database.

## Requirements.txt

This file contains the required external libraries/packages that are needed to run the website.
Use pip3 for installing the packages.