#TakeTheTrip — Платформа за Споделено Пътуване

Уеб приложение за организиране на споделени пътувания между шофьори и пътници. Проектът е създаден с цел лесно откриване на маршрути, намаляване на транспортните разходи и директна комуникация между потребителите.

---

## Основни функционалности

* **Профили и регистрация:**
  * Полето за автомобил е незадължително — подходящо както за шофьори, така и за пътници.
  * Персонални профили с опция за снимка, телефон и връзки към социални мрежи.
* **Управление на обяви:**
  * Публикуване на пътуване (маршрут, дата, час, цена и свободни места).
  * Интуитивен селектор за дата и час, съобразен с мобилни устройства.
  * Търсене и филтриране на налични обяви.
* **Система за отзиви:**
  * Оценяване и коментари между пътуващите след приключване на курс.

---

## Технологичен стек

* **Backend:** Python / Django
* **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
* **База данни:** SQLite (Development) / PostgreSQL (Production)
* **Production Environment:** Ubuntu Server, Nginx, Gunicorn, systemd

---

## Локално стартиране

1. **Клониране на репозиторито:**
   ```bash
   git clone https://github.com/MonsterGuti/TakeTheTrip-app.git
   cd TakeTheTrip-app
   ```

2. **Създаване и активиране на виртуална среда:**
   ```bash
   python -m venv venv
   
   # Windows:
   venv\Scripts\activate
   
   # Linux/macOS:
   source venv/bin/activate
   ```

3. **Инсталиране на библиотеки:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Миграции и стартиране:**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
   Приложението ще бъде достъпно на `http://127.0.0.1:8000/`.

---

## Деплой на production сървър

Команди за обновяване на живата среда:

```bash
cd /var/www/TakeTheTrip-app
source venv/bin/activate
git pull origin main
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart takethetrip
```

---

## Автор

**Мартин Гогуланов**
* GitHub: [@MonsterGuti](https://github.com/MonsterGuti)
* Live App: [takethetripapp.com](https://takethetripapp.com)