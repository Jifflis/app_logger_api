redis:
	redis-server --daemonize yes

start: redis
	flask run
