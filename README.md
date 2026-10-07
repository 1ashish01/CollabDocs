# CollabDocs

API-only collaborative document platform. Users create workspaces, invite members, write versioned documents, leave threaded comments, tag documents, and control access with role-based membership.

There is no frontend. Postman is the client.

**Demo video:** _placeholder — add the Loom or Google Drive link here before submission._

## Stack

- Python 3.13
- Django 6.1.2
- Django REST Framework 3.18.3
- python-decouple 3.8
- psycopg 3.3.6
- PostgreSQL (credentials loaded from `.env`; database server not created yet)

## Build progress

Checked after each step. Latest check: settings loaded from `.env`.

- [x] **Step 1 — Django project.** Virtual environment created with Python 3.13. `django-admin startproject config .` generated `manage.py` and the `config` package (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`) in the repository root.
- [x] **Step 2 — `core` app.** `python manage.py startapp core` created `core/` with `models.py`, `views.py`, `apps.py` (`CoreConfig`), `admin.py`, `tests.py`, and `migrations/__init__.py`.
- [x] **Step 3 — App registration and extra modules.** `core.apps.CoreConfig` is in `INSTALLED_APPS`. `core/serializers.py`, `core/urls.py`, `core/signals.py`, and `core/middleware.py` exist and are still empty.
- [x] **Step 4 — Ignore rules and env template.** `.gitignore` excludes `venv/`, `.env`, `__pycache__/`, `*.py[cod]`, `db.sqlite3`, and `.DS_Store`. `.env.example` lists `SECRET_KEY`, `DEBUG`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`.
- [x] **Step 5 — Pinned dependencies.** `requirements.txt` pins `Django==6.1.2`, `djangorestframework==3.18.3`, `python-decouple==3.8`, `psycopg==3.3.6`, `psycopg-binary==3.3.6`, plus `asgiref==3.12.1` and `sqlparse==0.6.0`.
- [x] **Step 6 — Load settings from `.env`.** `SECRET_KEY` and `DEBUG` use `config()`. `DATABASES` uses `django.db.backends.postgresql` and reads `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` from `.env`. `rest_framework` is in `INSTALLED_APPS`. The real `.env` stays untracked.
- [ ] **Step 7 — Models.** Write all 8 models in `core/models.py`.
- [ ] Serializers, viewsets, and `/api/` routes
- [ ] Middleware and Document `post_save` signal
- [ ] Postman collection for all 17 endpoints

## Current layout

```
CollabDocs/
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/
│   ├── migrations/
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── middleware.py
│   ├── models.py
│   ├── serializers.py
│   ├── signals.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── .env.example
├── .gitignore
├── manage.py
├── README.md
├── requirements.txt
└── venv/
```

`venv/` stays on this machine and will be listed in `.gitignore`. It is not part of the submission.

## Setup so far

From the repository root:

```bash
/opt/homebrew/bin/python3.13 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install django
django-admin startproject config .
python manage.py startapp core
pip install djangorestframework python-decouple "psycopg[binary]"
pip freeze > requirements.txt
```

The trailing `.` keeps `manage.py` in this folder. `DJANGO_SETTINGS_MODULE` is `config.settings`. The app config class is `core.apps.CoreConfig`.
