# Al_Murad Logistics App

## Current setup
- Django 6.0 project
- SQLite database (`db.sqlite3`) is ignored from Git
- Dependencies listed in `requirements.txt`
- `.gitignore` already created
- Git repo initialized locally

## What you need next
1. Create a GitHub repository for this project.
2. Add the repository as a remote and push the code.
3. Deploy on PythonAnywhere using the GitHub repository.

## Push to GitHub
```powershell
cd "C:\Users\welcome\Desktop\Al_Murad"
git branch -M main
git remote add origin https://github.com/sheikhharis-gif/al_murad.git
git add .
git commit -m "chore: add PythonAnywhere deployment files"
git push -u origin main
```

> If the remote already exists, use `git remote set-url origin <repo-url>` instead.

## PythonAnywhere deployment (basic)
1. Create a PythonAnywhere account and log in.
2. Create a new web app.
   - Choose `Manual configuration`
   - Choose `Python 3.11` or `Python 3.10`
3. Open a Bash console on PythonAnywhere.
4. Clone your GitHub repo:
   ```bash
   git clone https://github.com/sheikhharis-gif/al_murad.git
   cd al_murad
   ```
5. Create a virtualenv:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
6. Update `logistics_project/settings.py`:
   - Set `DEBUG = False`
   - Add your PythonAnywhere domain to `ALLOWED_HOSTS`, for example:
     ```python
     ALLOWED_HOSTS = ['yourusername.pythonanywhere.com']
     ```
7. Configure the web app:
   - Set the working directory to `/home/yourusername/<your-repo>`
   - Set the WSGI file to point to `logistics_project/wsgi.py`
   - Configure static files if needed:
     - URL `/static/` → directory `/home/yourusername/<your-repo>/static`
8. Run database migrations:
   ```bash
   source venv/bin/activate
   cd /home/yourusername/<your-repo>
   python manage.py migrate
   python manage.py createsuperuser
   ```
9. Reload the PythonAnywhere web app.

## Notes
- `db.sqlite3` is ignored, so the remote site will start with a fresh database unless you upload your local DB file manually.
- If you want to preserve existing data, upload `db.sqlite3` separately to PythonAnywhere and do not run migrations on it without backup.
- For production, use a real database like MySQL or PostgreSQL instead of SQLite.

## Quick check
After deployment, verify:
- `/admin/` works
- `/trips/` works
- `/trips/export/` downloads Excel
- `/trips/export/pdf/` downloads PDF
- `/jobs/invoice/1/` returns an invoice PDF (if job 1 exists)
