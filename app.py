import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from icalendar import Calendar, Event

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assignments.db'
db = SQLAlchemy(app)


class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    is_complete = db.Column(db.Boolean, default=False)
    description = db.Column(db.String(500))
    link = db.Column(db.String(200))


class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text, nullable=False)


class CalendarSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    calendar_url = db.Column(db.String(255), nullable=True)


@app.route('/')
def index():
    assignments = Assignment.query.all()
    return render_template('index.html', assignments=assignments)


@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
    description = request.form.get('description', '')
    link = request.form.get('link', '')
    is_complete = 'complete' in request.form

    assignment = Assignment(name=name, due_date=due_date, description=description, link=link, is_complete=is_complete)
    db.session.add(assignment)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/edit/<int:id>')
def edit(id):
    assignment = Assignment.query.get(id)
    return render_template('edit.html', assignment=assignment)


@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    assignment = Assignment.query.get(id)
    assignment.name = request.form['name']
    assignment.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
    assignment.description = request.form.get('description', '')
    assignment.link = request.form.get('link', '')
    assignment.is_complete = 'complete' in request.form
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/delete/<int:id>')
def delete(id):
    assignment = Assignment.query.get(id)
    db.session.delete(assignment)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/fetch_calendar')
def fetch_calendar():
    calendar_url = CalendarSettings.query.first().calendar_url

    if not calendar_url:
        return jsonify({'message': 'No calendar URL saved!'}), 400

    try:
        response = requests.get(calendar_url)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

        calendar_data = response.text

        # Save to the database
        event = CalendarEvent(data=calendar_data)
        db.session.add(event)
        db.session.commit()

        # Process and add assignments from blackboard
        process_and_add_assignments(calendar_data)

        return calendar_data, 200
    except requests.exceptions.RequestException as e:
        return f'Error fetching data: {e}', 500


@app.route('/get_calendar_url')
def get_calendar_url():
    calendar_settings = CalendarSettings.query.first()

    if calendar_settings:
        return jsonify({'calendar_url': calendar_settings.calendar_url})
    else:
        return jsonify({'calendar_url': None})


@app.route('/save_calendar_url', methods=['POST'])
def save_calendar_url():
    data = request.get_json()
    calendar_url = data.get('calendar_url')

    if calendar_url:
        calendar_settings = CalendarSettings.query.first()

        if calendar_settings:
            calendar_settings.calendar_url = calendar_url
        else:
            calendar_settings = CalendarSettings(calendar_url=calendar_url)

        db.session.add(calendar_settings)
        db.session.commit()

        return jsonify({'message': 'Calendar URL saved successfully.'}), 200
    else:
        return jsonify({'message': 'No calendar URL provided.'}), 400


@app.route('/get_assignments', methods=['GET'])
def get_assignments():
    assignments = Assignment.query.order_by(Assignment.due_date.desc()).all()

    assignments_list = [
        {'name': assignment.name, 'due_date': assignment.due_date, 'is_complete': assignment.is_complete} for assignment
        in assignments]
    return jsonify(assignments_list)


@app.route('/clear_all', methods=['DELETE'])
def clear_all():
    try:
        # Delete all assignments from the database
        Assignment.query.delete()
        db.session.commit()
        return jsonify({'message': 'All assignments deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Route to update completion status
@app.route('/complete/<int:assignment_id>', methods=['POST'])
def complete(assignment_id):
    try:
        assignment = Assignment.query.get(assignment_id)
        if assignment:
            # Toggle the completion status
            assignment.is_complete = not assignment.is_complete
            db.session.commit()
            response_data = {'message': 'Completion status updated successfully', 'is_complete': assignment.is_complete}
            return jsonify(response_data), 200
        else:
            response_data = {'error': 'Assignment not found'}
            return jsonify(response_data), 404
    except Exception as e:
        db.session.rollback()
        response_data = {'error': str(e)}
        return jsonify(response_data), 500


def process_and_add_assignments(calendar_data):
    cal = Calendar.from_ical(calendar_data)

    for component in cal.walk():
        if component.name == 'VEVENT':
            assignment_name = str(component.get('summary', ''))
            assignment_due_date = component.get('dtstart').dt

            # Check if the assignment already exists in the database
            existing_assignment = Assignment.query.filter_by(name=assignment_name).first()

            if not existing_assignment:
                # If the assignment doesn't exist, add it to the database
                assignment = Assignment(
                    name=assignment_name,
                    due_date=assignment_due_date,
                    is_complete=False  # You can set the completion status as needed
                )
                db.session.add(assignment)

    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True, host="0.0.0.0", port=8000)
