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

### Suggested deployment
- Run FastAPI as application server using uvicorn
- Run workers using supervisor


### Supabase trigger setup

```
-- Create function
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, raw_app_meta_data, raw_user_meta_data)
  VALUES (
    new.id,
    new.raw_app_meta_data,
    new.raw_user_meta_data
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Ensure the trigger is set up (if not already)
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```