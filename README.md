# CollabDocs

CollabDocs is an API-only collaborative document platform built with Django REST Framework and PostgreSQL.

Users can create workspaces, manage workspace members, create and update documents with version history, add threaded comments, associate tags, and view document audit logs.

There is no frontend. Postman is used to test the API.

## Technology Stack

- Python 3.14
- Django 6.1.1
- Django REST Framework 3.18.1
- PostgreSQL 16
- psycopg 3.3.6
- python-dotenv 1.2.4
- Docker Compose

## Project Structure

- `config/` - Django project settings and URL configuration
- `collabdocs/` - Models, serializers, views, middleware, signals, tests, and migrations
- `docker-compose.yml` - PostgreSQL service configuration
- `.env.example` - Example environment variables
- `requirements.txt` - Python dependencies

## Prerequisites

- Python compatible with the installed Django version
- Docker Desktop with Docker Compose
- Git

## Setup

1. Clone this repository and open its directory.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt


