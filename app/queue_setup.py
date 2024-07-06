# queue_setup.py
from rq import Queue
from redis import Redis

thumbnail_queue = Queue('thumbnails', connection=Redis())