# meduzzen_internship

Start the application by running `main.py`.

You can access the healthcheck endpoint by navigating to http://localhost:8000 once the app is running.

Navigate to `/tests` to run tests. You can use `pytest` for it.

To launch the application within `Docker`, build an image off of `Dockerfile` and launch a container!

If you're making changes to database models and schemas, don't forget to apply migrations. For that, you should check if your changes are imported in `alembic/env.py`, and then run `alembic revision --autogenerate -m "migration name"`.
