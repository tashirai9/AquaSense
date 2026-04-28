AquaSense 

A Flask-based web application for monitoring water usage, detecting anomalies, and promoting conservation.

Features

*  Dashboard with usage analytics
*  Anomaly detection (ML-based)
*  Alerts and threshold monitoring
*  Weather integration
*  Gamification (streaks & scores)

 Tech Stack

* Python (Flask)
* SQLite
* HTML, CSS, JavaScript
* Machine Learning (custom modules)

 How to Run

```bash
git clone https://github.com/tashirai9/aquasense.git
cd aquasense
pip install -r requirements.txt
python -m flask --app aquasense.app run
```

Then open:
http://127.0.0.1:5000

 Project Structure

```
aquasense/
│── blueprints/
│── ml/
│── models/
│── utils/
│── app.py
│── config.py
templates/
static/
```

 Notes

* Add your API keys in `config.py`
* Database is SQLite (`database.db`)

---

Made with using Flask
