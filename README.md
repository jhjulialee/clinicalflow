# ClinicalFlow: Clinical Data Request Tracker

ClinicalFlow is a full-stack productivity application for clinical data operations workflows. It allows authenticated users to create, organize, prioritize, track, and document fictional clinical data requests in one secure workspace.

The project directly addresses the project pitch: requests for reports, data-quality checks, dashboard refreshes, and data extracts can otherwise be scattered across email, chat, spreadsheets, and meetings. ClinicalFlow provides a structured intake and tracking workflow:

```text
Sign up / Log in → Create request → Prioritize and update → Add notes → Complete and retain history
```

> **Privacy and scope:** ClinicalFlow contains only fictional or synthetic data. Never enter real patient information, protected health information (PHI), or clinical-system credentials.

## Live application

- Frontend: _Add your deployed Vercel/Netlify URL here_
- API: _Add your deployed Render URL here_
- Project brief: [`docs/ClinicalFlow_Productivity_App_Pitch.md`](docs/ClinicalFlow_Productivity_App_Pitch.md)

## Why this project

Clinical data analysts and research stakeholders need a centralized way to manage operational requests. ClinicalFlow reduces friction by preserving request details, priority, status, due date, ownership, and progress notes in a searchable workflow.

## Features

### Authentication and authorization

- Account signup, login, persistent session check, and logout.
- Password hashes generated with Werkzeug; plaintext passwords are never saved.
- Protected frontend routes and backend authentication checks.
- Ownership-based access control: each user can read, update, and delete **only their own** requests and notes.
- `401 Unauthorized` for unauthenticated requests and `403 Forbidden` for attempts to access another user’s record.

### Productivity workflow

- Full CRUD for **Data Requests**: create, view, update, and delete.
- Full CRUD for **Request Notes**: create, view, edit, and delete.
- Two relational resources: `User → DataRequest → RequestNote`.
- Track request type, priority, workflow status, due date, and completion time.
- Search and filter requests by title/description, status, priority, and type.
- Pagination for requests and notes.
- Dashboard metrics: New, In Progress, Blocked, Completed, and Overdue requests.
- Clear loading, empty, success, client validation, API validation, and error states.

## Technology

| Layer | Technology |
|---|---|
| Frontend | React, Vite, React Router, CSS |
| Backend | Python, Flask, Flask-SQLAlchemy, Flask-Migrate |
| Database | PostgreSQL in production; SQLite fallback for quick local exploration only |
| Authentication | Flask signed-cookie sessions, Werkzeug password hashing |
| Testing | Pytest with a temporary SQLite test database |
| Deployment | Render Blueprint for Flask + PostgreSQL; Vercel/Netlify optional for React |

## Data model

```text
User (1) ───< DataRequest (1) ───< RequestNote
                 │                    │
                 └── owner_id          └── owner_id
```

- A user owns many data requests.
- A data request belongs to one user and has many notes.
- A user owns many notes.
- Backend routes verify ownership before any individual record is read, updated, or deleted.

## API endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/signup` | Create an account and begin a session |
| POST | `/api/login` | Log into an existing account |
| DELETE | `/api/logout` | End the current session |
| GET | `/api/check_session` | Return the signed-in user or `401` |

### Data requests

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/requests?page=1&per_page=10` | Paginated list of the current user’s requests |
| POST | `/api/requests` | Create a request owned by the current user |
| GET | `/api/requests/:id` | Get an owned request and paginated notes |
| PATCH | `/api/requests/:id` | Update an owned request |
| DELETE | `/api/requests/:id` | Delete an owned request and its notes |

### Request notes

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/requests/:id/notes?page=1&per_page=5` | Paginated notes for an owned request |
| POST | `/api/requests/:id/notes` | Create a note on an owned request |
| GET | `/api/notes/:id` | Get an owned note |
| PATCH | `/api/notes/:id` | Update an owned note |
| DELETE | `/api/notes/:id` | Delete an owned note |

## Local setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ recommended

### 1. Clone and configure environment variables

```bash
git clone https://github.com/YOUR-USERNAME/clinicalflow.git
cd clinicalflow
cp .env.example .env
```

Update `.env` with your local PostgreSQL connection string and a long random `SECRET_KEY`.

### 2. Create the database

```bash
createdb clinicalflow
```

### 3. Start the Flask API

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app server.wsgi db upgrade
flask --app server.wsgi seed
flask --app server.wsgi run --debug
```

The API runs at `http://127.0.0.1:5000`.

### 4. Start the React client

In a second terminal:

```bash
cd client
npm install
npm run dev
```

Open the Vite URL, normally `http://127.0.0.1:5173`.

### 5. Run tests

```bash
pytest
```

## Demo workflow

1. Create Account with an email you control for the local demo.
2. Create a fictional data request such as “Monthly enrollment report.”
3. Change its status to “In Progress,” set a due date, and update the priority.
4. Add a progress note, edit it, and delete it.
5. Use the search/filter controls and pagination.
6. Log out and confirm protected pages redirect to Login.
7. Create a second account; verify its request list does not reveal the first account’s records.

## Deployment

### Backend and PostgreSQL on Render

1. Push this project to a public GitHub repository.
2. In Render, create a Blueprint from the repository and select `render.yaml`.
3. Set `CORS_ORIGIN` to the deployed client URL.
4. Run migrations and seed optional demo data using the Render Shell:

```bash
flask --app server.wsgi db upgrade
flask --app server.wsgi seed
```

### Frontend on Vercel or Netlify

Deploy the `client` directory and configure:

```text
VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

For cross-origin session cookies in production, use HTTPS, configure the exact deployed client origin in `CORS_ORIGIN`, and set an appropriate secure-cookie configuration for your chosen deployment topology.

## Project brief

The final pitch is included at [`docs/ClinicalFlow_Productivity_App_Pitch.md`](docs/ClinicalFlow_Productivity_App_Pitch.md). It defines the business problem, users, data model, technical strategy, time-boxed plan, risks, and rubric alignment.

## Future improvements

- Separate manager/team workflows with carefully defined permission policies.
- Dashboard reporting by request type and turnaround time.
- Email reminders for upcoming due dates.
- File metadata/attachments with secure storage.
- Optional AI request-summary assistance using fictional data only.
- Expanded automated frontend and API test coverage.

## Git hygiene

The repository intentionally ignores secrets, virtual environments, client dependencies, build output, caches, local database files, and editor artifacts. Commit in small, descriptive increments, for example:

```text
feat: configure Flask app and PostgreSQL
feat: add signup login logout and session check
feat: add ownership-protected request CRUD
feat: add note CRUD and pagination
feat: build dashboard and protected React routes
test: verify authorization and request pagination
docs: complete setup and deployment guide
```
