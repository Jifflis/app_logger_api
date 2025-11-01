export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1

redis:
	redis-server --daemonize yes

start: redis
	flask run
