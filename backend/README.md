# RehabConnect Flask Prototype

## Setup

1. Make sure Python is installed (3.7+ recommended).
2. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install flask qrcode[pil]
```

## Run

```bash
python rehabconnect.py
```

Open `http://127.0.0.1:5000/` in a browser.

## Routes

- `/` redirects to current patient schedule (`/patient/<patient_id>`)
- `/patient/<patient_id>` shows schedule details
- `/update` edit patient times via a form (POST saves to `schedule.json`)
- `/qr/<patient_id>` shows a QR code page
- `/qr_image/<patient_id>` returns QR code PNG for `http://localhost:5000/patient/<patient_id>`

## Data file

- `schedule.json` contains:
  - `patient_id`
  - `pt_time`
  - `ot_time`
  - `st_time`

## Notes

- The app overwrites `schedule.json` on updates.
- No authentication is included, for simplicity.
