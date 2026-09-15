# TakeTheTrip — Ride-Sharing Platform

A modern web application designed to connect drivers and passengers traveling along similar routes. The platform simplifies trip discovery, reduces travel costs, and facilitates direct communication between users.

---

## Key Features

* **User Accounts & Profiles:**
  * Optional vehicle registration — tailored for both drivers and passengers.
  * Personalized profiles with profile picture upload, contact details, and social media links (Facebook / Instagram).
* **Trip Management:**
  * Publish new rides with detailed route information, departure dates, seat capacity, and pricing.
  * Mobile-optimized date and time selectors for seamless trip creation.
  * Search and filter options for available trips.
* **Review & Rating System:**
  * Ratings and comments between drivers and passengers following completed trips.

---

## Tech Stack

* **Backend:** Python / Django Framework
* **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
* **Database:** SQLite (Development) / PostgreSQL (Production)
* **Production Deployment:** Ubuntu Server, Nginx, Gunicorn, systemd

---

## Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MonsterGuti/TakeTheTrip-app.git
   cd TakeTheTrip-app
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows:
   venv\Scripts\activate
   
   # Linux/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations and start server:**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
   Access the application at `http://127.0.0.1:8000/`.

---

## Production Deployment Workflow

Commands for updating the live environment on the server:

```bash
cd /var/www/TakeTheTrip-app
source venv/bin/activate
git pull origin main
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart takethetrip
```

---

## Author

**Martin Gogulanov**
* GitHub: [@MonsterGuti](https://github.com/MonsterGuti)
* Live App: [takethetripapp.com](https://takethetripapp.com)