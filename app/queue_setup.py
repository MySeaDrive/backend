# queue_setup.py
from rq import Queue
from redis import Redis

thumbnail_queue = Queue('thumbnails', connection=Redis())
color_correction_queue = Queue('color_correction', connection=Redis(), default_timeout=600)