import os
import io
import json
import qrcode
from flask import Flask, render_template, request, redirect, url_for, abort, send_file

# Create Flask app instance
app = Flask(__name__)

# Path to the schedule JSON file stored next to this script
SCHEDULE_FILE = os.path.join(os.path.dirname(__file__), 'schedule.json')


def load_schedule():
    """Load schedule data from schedule.json and return a dict."""
    try:
        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def save_schedule(schedule_data):
    """Save schedule_data dict back to schedule.json."""
    with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
        json.dump(schedule_data, f, indent=2)


@app.route('/')
def home():
    """Home route. Redirect to patient's page using schedule.json data."""
    schedule = load_schedule()
    if not schedule:
        return '<h1>No schedule available</h1><p>Please create schedule.json.</p>'

    patient_id = schedule.get('patient_id', '').strip()
    if not patient_id:
        return '<h1>Invalid schedule data</h1>'

    return redirect(url_for('patient', patient_id=patient_id))


@app.route('/patient/<patient_id>')
def patient(patient_id):
    """Show the schedule for a given patient ID."""
    schedule = load_schedule()
    if not schedule:
        abort(404, description='Schedule data not found.')

    current_id = str(schedule.get('patient_id', '')).strip()
    if current_id != str(patient_id):
        return (
            f'<h1>Patient Not Found</h1>'
            f'<p>No schedule exists for patient ID {patient_id}.</p>'
            f'<p>Try patient ID {current_id}.</p>'
        ), 404

    return render_template('schedule.html', schedule=schedule)


@app.route('/qr_image/<patient_id>')
def qr_image(patient_id):
    """Generate and return a QR code PNG for the patient schedule URL."""
    schedule = load_schedule()
    if not schedule or str(schedule.get('patient_id', '')) != str(patient_id):
        abort(404, description='Patient schedule not found.')

    target_url = f'http://localhost:5000/patient/{patient_id}'

    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(target_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='image/png',
        as_attachment=False,
        download_name=f'patient_{patient_id}_qr.png'
    )


@app.route('/qr/<patient_id>')
def qr_page(patient_id):
    """Render a page that shows the QR code image for this patient."""
    schedule = load_schedule()
    if not schedule or str(schedule.get('patient_id', '')) != str(patient_id):
        abort(404, description='Patient schedule not found.')

    return render_template('qr.html', patient_id=patient_id)


@app.route('/update/<patient_id>', methods=['GET', 'POST'])
def update(patient_id):
    """Display the update form (GET) and save changes (POST)."""
    schedule = load_schedule() or {}

    if request.method == 'POST':
        # Read form fields and update schedule data
        pt_time = request.form.get('pt_time', '').strip()
        ot_time = request.form.get('ot_time', '').strip()
        st_time = request.form.get('st_time', '').strip()

        if not pt_time or not ot_time or not st_time:
            return render_template(
                'update.html',
                schedule=schedule,
                error='All fields are required. Please complete the form.'
            )

        # Build updated schedule
        schedule = {
            'patient_id': patient_id,
            'pt_time': pt_time,
            'ot_time': ot_time,
            'st_time': st_time,
        }

        save_schedule(schedule)
        return redirect(url_for('patient', patient_id=patient_id))

    # GET request: prefill with current schedule
    return render_template('update.html', schedule=schedule)



if __name__ == '__main__':
    # Start Flask development server
    app.run(host="0.0.0.0", port=10000) 
