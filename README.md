
# Warbler

A full stack web application Twitter clone built with Flask. Users can create accounts, write 'messages' (tweets), like/unlike others messages, and follow/unfollow other users.

Demo: https://rb-warbler.onrender.com/
## Tech Stack
![flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)

![python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

![alt text](https://img.shields.io/badge/-SQLAlchemy-F40D12?logo=sqlalchemy&logoColor=white&style=for-the-badge)

![postgresql](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)



## Features
- User registration, autentication, authorization
- Post, like, unlike messages
- Follow/unfollow other users
- RESTful API
- 99% test coverage
## Run Locally
Create Python virtual environment and activate:

    python3 -m venv venv
    source venv/bin/activate

Install dependences from requirements.txt:

    pip install -r requirements.txt

Setup the database:

    createdb warbler
    python seed.py

Create an .env file to hold configurations:

    SECRET_KEY=abc123
    DATABASE_URL=postgresql:///warbler

Start the server:

    flask run



## Future Features

- AJAX for liking/unliking, creating messages
- Jinja macros to clean up repetitive code
- Optimize queries
- Change password form
- Private accounts
- Block users
- DM other users



## Authors

- [Ross Brown](https://www.github.com/ross-brown)
- [Daniel Zych](https://www.github.com/danjzych)

