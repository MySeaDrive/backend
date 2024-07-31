### Pre-requisites

- Supabase docker for
    - Postgres DB
    - Auth

- Minio docker for object storage on localhost
- Redis for background jobs


### Environment vars to be placed in `secrets/.env`

```
FRONTEND_URL=

DB_CONNECTION_STRING=

SUPABASE_URL=
SUPABASE_KEY=
JWT_SECRET_KEY=

STORAGE_ENDPOINT_URL=
STORAGE_APPLICATION_KEY_ID=
STORAGE_APPLICATION_KEY=o
STORAGE_BUCKET=
```

### Standard stuff
Create a python virtual env and run
```
$ pip install -r requirements.txt
$ fastapi dev --port 5000 app/main.py
```

Boot workers
```
$ rq worker thumbnails
$ rq worker color_correction
```

Running on MacOS would need you to set `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES`