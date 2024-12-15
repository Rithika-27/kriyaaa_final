from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response,jsonify,send_from_directory
from pymongo import MongoClient
from reportlab.pdfgen import canvas  # Using ReportLab for PDF generation
from reportlab.lib.pagesizes import letter
import os  # For managing file paths
from PyPDF2 import PdfReader, PdfWriter
from xhtml2pdf import pisa
import io
from io import BytesIO
import PyPDF2  
from datetime import datetime
import uuid
import shutil
from PyPDF2 import PdfMerger

app = Flask(__name__)
app.secret_key = 'xyz1234nbg789ty8inmcv2134'  # Make sure this key is kept secure

# MongoDB connection
MONGO_URI = "mongodb+srv://Entries:ewp2025@cluster0.1tuj7.mongodb.net/event-kriya?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["event-kriya"]
event_collection = db["event-entries"]
workshop_collection=db["workshop-entries"]
presentation_collection=db["presentation-entries"]


USERNAME = 'admin'
PASSWORD = 'admin'
# Main route for home


# Home route (index page)
@app.route('/index')
def index():
    if not session.get('logged_in'):  # Check if the user is logged in
        return redirect(url_for('login'))  # If not logged in, redirect to login page
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validate username and password
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True  # Set the session to indicate the user is logged in
            return redirect(url_for('index'))  # Redirect to the index page (home)
        else:
            flash("Invalid username or password!", "error")  # Flash error message

    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)  # Remove the 'logged_in' session variable
    return redirect(url_for('login'))  # Redirect to login page

@app.route('/search_event_admin', methods=['GET', 'POST'])
def search_event_admin():
    if request.method == 'POST':
        event_id = request.form.get('event_id')  # Correct way to get event_id from form data
  
        if not event_id:
            return render_template('index.html', error="Please enter an ID to search.")

        # Check if the search ID starts with "WKSP" for workshop
        if event_id.startswith("WKSP"):
            # Fetch workshop data from the database
            workshop = workshop_collection.find_one({"workshop_id": event_id})
            if workshop:
                return render_template('edit_workshop.html', workshop=workshop, error=None)
            else:
                return render_template('edit_workshop.html', workshop=None, error="Workshop not found.")

        # Check if the search ID starts with "EVNT" for event
        elif event_id.startswith("EVNT"):
            # Fetch event data from the database
            event = event_collection.find_one({"event_id": event_id})
            if event:
                return render_template('edit_event.html', event=event, error=None)
            else:
                return render_template('edit_event.html', event=None, error="Event not found.")

        # Check if the search ID starts with "PPST" for presentation
        elif event_id.startswith("PPST"):
            # Fetch presentation data from the database
            presentation = presentation_collection.find_one({"presentation_id": event_id})
            if presentation:
                return render_template('edit_presentation.html', presentation=presentation, error=None)
            else:
                return render_template('edit_presentation.html', presentation=None, error="Presentation not found.")

        # If the ID format is invalid
        return render_template('index.html', error="Invalid ID format. Please enter a valid Event ID, Workshop ID, or Presentation ID.")

    # Render the search form page for GET requests
    return render_template('search_event.html')  

@app.route('/save_workshop', methods=['POST'])
def save_workshop():
    try:
        # Parse form data
        workshop_data = request.form

        # Get the workshop ID (assumed to be a unique identifier)
        workshop_id = workshop_data.get('workshop_id')
        if not workshop_id:
            return jsonify({"error": "Workshop ID is required."}), 400

        # Fetch the existing workshop data from the database
        existing_workshop = workshop_collection.find_one({"workshop_id": workshop_id})
        if not existing_workshop:
            return jsonify({"error": "Workshop not found."}), 404

        # Prepare the updated data
        updated_workshop = existing_workshop.copy()

        # Update only the fields present in the form data
        updated_workshop['association_name'] = workshop_data.get('association_name', existing_workshop['association_name'])
        updated_workshop['workshop_name'] = workshop_data.get('workshop_name', existing_workshop['workshop_name'])
        updated_workshop['workshop']['description'] = workshop_data.get('description', existing_workshop['workshop']['description'])
        updated_workshop['workshop']['prerequisites'] = workshop_data.get('prerequisites', existing_workshop['workshop']['prerequisites'])
        updated_workshop['workshop']['session_count'] = int(workshop_data.get('session_count', existing_workshop['workshop']['session_count']))

        # Update details
        for key, value in existing_workshop['details'].items():
            updated_workshop['details'][key] = workshop_data.get(f'details_{key}', value)

        # Update form fields
        for key, value in existing_workshop['form'].items():
            updated_workshop['form'][key] = workshop_data.get(f'form_{key}', value)

        # Update the database with the modified workshop data
        workshop_collection.replace_one({"workshop_id": workshop_id}, updated_workshop)

        return jsonify({"message": "Workshop updated successfully."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Save event route
@app.route('/save_event', methods=['POST'])
def save_event():
    try:
        # Parse form data
        event_data = request.form

        # Get the event ID (assumed to be a unique identifier)
        event_id = event_data.get('event_id')
        if not event_id:
            return jsonify({"error": "Event ID is required."}), 400

        # Fetch the existing event data from the database
        existing_event = event_collection.find_one({"event_id": event_id})
        if not existing_event:
            return jsonify({"error": "Event not found."}), 404

        # Prepare the updated data
        updated_event = existing_event.copy()

        # Update only the fields present in the form data
        updated_event['association_name'] = event_data.get('association_name', existing_event['association_name'])
        updated_event['event_name'] = event_data.get('event_name', existing_event['event_name'])
        updated_event['event']['tagline'] = event_data.get('tagline', existing_event['event']['tagline'])
        updated_event['event']['about'] = event_data.get('about', existing_event['event']['about'])
        updated_event['event']['round_count'] = int(event_data.get('round_count', existing_event['event']['round_count']))

        # Update details
        for key, value in existing_event['details'].items():
            updated_event['details'][key] = event_data.get(f'details_{key}', value)

        # Update form fields
        for key, value in existing_event['form'].items():
            updated_event['form'][key] = event_data.get(f'form_{key}', value)

        # Update the database with the modified event data
        event_collection.replace_one({"event_id": event_id}, updated_event)

        return jsonify({"message": "Event updated successfully."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/save_presentation', methods=['POST'])
def save_presentation():
    try:
        # Parse form data
        presentation_data = request.form

        # Get the presentation ID (assumed to be a unique identifier)
        presentation_id = presentation_data.get('presentation_id')
        if not presentation_id:
            return jsonify({"error": "Presentation ID is required."}), 400

        # Fetch the existing presentation data from the database
        existing_presentation = presentation_collection.find_one({"presentation_id": presentation_id})
        if not existing_presentation:
            return jsonify({"error": "Presentation not found."}), 404

        # Prepare the updated data
        updated_presentation = existing_presentation.copy()

        # Update association and presentation details
        updated_presentation['association_name'] = presentation_data.get('association_name', existing_presentation['association_name'])
        updated_presentation['presentation_name'] = presentation_data.get('presentation_name', existing_presentation['presentation_name'])

        # Update details section
        updated_presentation['details'] = {}
        for key, value in existing_presentation['details'].items():
            updated_presentation['details'][key] = presentation_data.get(f'details[{key}]', value)

        # Update presentation information
        updated_presentation['presentation']['event_description'] = presentation_data.get('event_description', existing_presentation['presentation']['event_description'])
        updated_presentation['presentation']['topics_and_theme'] = presentation_data.get('topics_and_theme', existing_presentation['presentation']['topics_and_theme'])
        updated_presentation['presentation']['event_rules'] = presentation_data.get('event_rules', existing_presentation['presentation']['event_rules'])

        # Update form details
        updated_presentation['form'] = {}
        for key, value in existing_presentation['form'].items():
            updated_presentation['form'][key] = presentation_data.get(f'form[{key}]', value)

        # Update the database with the modified presentation data
        presentation_collection.replace_one({"presentation_id": presentation_id}, updated_presentation)

        return jsonify({"message": "Presentation updated successfully."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Main route for home
@app.route('/')
def home():
    # session.clear()  # Clear all session data for a new event
    return render_template('home.html')
@app.route('/event-info', methods=['GET', 'POST'])
def event_info():
    if request.method == 'POST':
        # Collect event details and store in session
        event_details = {
            'association_name': request.form['association_name'],
            'event_name': request.form['event_name']
        }
        session['event_info'] = event_details
        return redirect(url_for('event_instructions'))

    return render_template('event_info.html')

    

@app.route('/event_instructions', methods=['GET', 'POST'])
def event_instructions():
    if request.method == 'POST':
        return redirect(url_for('event_detail'))
    return render_template('event_instruction.html')

# Event Details Form
@app.route('/event-detail', methods=['GET', 'POST'])
def event_detail():
    if request.method == 'POST':
        # Collect event details and store in session
        event_details = {
            'secretary_name': request.form['secretary_name'],
            'secretary_roll_number': request.form['secretary_roll_number'],
            'secretary_mobile': request.form['secretary_mobile'],
            'convenor_name': request.form['convenor_name'],
            'convenor_roll_number': request.form['convenor_roll_number'],
            'convenor_mobile': request.form['convenor_mobile'],
            'faculty_advisor_name': request.form['faculty_advisor_name'],
            'faculty_advisor_designation': request.form['faculty_advisor_designation'],
            'faculty_advisor_contact': request.form['faculty_advisor_contact'],
            'judge_name': request.form['judge_name'],
            'judge_designation': request.form['judge_designation'],
            'judge_contact': request.form['judge_contact']
        }
        session['event_details'] = event_details
        return redirect(url_for('event_page'))
    return render_template('event_detail.html')

# Event Data Form
@app.route('/event', methods=['GET', 'POST'])
def event_page():
    if request.method == 'POST':
        # Collect event data and store in session
        event_data = {
            'day_1': 'day_1' in request.form,
            'day_2': 'day_2' in request.form,
            'day_3': 'day_3' in request.form,
            'technical_event':'technical_event' in request.form,
            'non_technical_event':'non_technical_event' in request.form,
            'two_days': request.form.get('two_days'),
            'rounds': request.form.get('rounds'),
            'participants': request.form.get('participants'),
            'individual': 'individual' in request.form,
            'team': 'team' in request.form,
            'team_min': request.form.get('team_min'),
            'team_max': request.form.get('team_max'),
            'halls_required': request.form.get('halls_required'),
            'preferred_halls': request.form.get('preferred_halls'),
            'slot': request.form.get('slot'),
            'extension_boxes': request.form.get('extension_boxes'),
            'event_description': request.form.get('event_description'),
            'event_location': request.form.get('event_location')
        }
        session['event_data'] = event_data
        return redirect(url_for('items_page'))
    return render_template('event.html')


@app.route('/items', methods=['GET', 'POST'])
def items_page():
    if 'event_items' not in session:
        session['event_items'] = []

    if request.method == 'POST':
        # Collect item data from the form and store it in the session
        try:
            item_data = {
                "sno": request.form.get("sno"),
                "item_name": request.form.get("item_name"),
                "quantity": int(request.form.get("quantity")),
                "price_per_unit": float(request.form.get("price_per_unit")),
                "total_price": int(request.form.get("quantity")) * float(request.form.get("price_per_unit"))
            }

            # Validate required fields
            if not item_data["item_name"] or not item_data["quantity"]:
                flash("Item name and quantity are required.")
                return redirect(url_for('items_page'))

            # Append item to session
            session['event_items'].append(item_data)
            flash("Item added successfully!")
            return redirect(url_for('event_summary'))
        except ValueError:
            flash("Please enter valid numeric values for quantity and price.")
            return redirect(url_for('items_page'))

    return render_template('items.html', event_items=session['event_items'])

# Event Summary Form
@app.route('/event_summary', methods=['GET', 'POST'])
def event_summary():
    if request.method == 'POST':
        event_name = request.form.get('name')
        tagline = request.form.get('tagline')
        about = request.form.get('about')
        rounds = []

        round_count = int(request.form.get('round_count', 0))
        for i in range(round_count):
            rounds.append({
                "round_no": i + 1,
                "name": request.form.get(f'round_name_{i}'),
                "description": request.form.get(f'round_description_{i}'),
                "rules": request.form.get(f'round_rules_{i}')
            })

        session['event_summary'] = {
            "name": event_name,
            "tagline": tagline,
            "about": about,
            "rounds": rounds
        }
        return redirect(url_for('preview'))
    return render_template('event_form.html')


@app.route('/preview', methods=['GET'])
def preview():
    try:
        # Retrieve event details, event data, event items, and event form data from session
        event_details = session.get('event_details', {})
        event_data = session.get('event_data', {})
        event_items = session.get('event_items', [])
        event_form_data = session.get('event_form_data', {})

        # Pass all the data to the template
        return render_template('preview.html', 
                               event_details=event_details, 
                               event_data=event_data,
                               event_items=event_items,
                               event_form_data=event_form_data)
    except Exception:
        return jsonify({"status": "error", "message": "Error retrieving preview data"}), 500
@app.route('/submit_event', methods=['POST'])
def submit_event():
    try:
        # Get the request JSON data
        all_event_data = request.get_json()  # Correct method to get JSON data
        event_details = all_event_data.get('eventDetails')
        event_data = all_event_data.get('eventData')
        event_items = all_event_data.get('eventItems')  # Correct field name should match
        event_summary = all_event_data.get('eventFormData')
        association_name=all_event_data.get('association_name')
        event_name=all_event_data.get('event_name')

        # Log the received data to ensure it's correct
        print("Received event details:", event_details)
        print("Received event data:", event_data)
        print("Received event items:", event_items)  # Log items
        print("Received event summary:", event_summary)

        # Generate a new event ID based on the last event ID in the database
        existing_event = event_collection.find_one(sort=[("event_id", -1)])
        if existing_event and "event_id" in existing_event:
            last_event_num = int(existing_event["event_id"][4:])
            new_event_id = f"EVNT{last_event_num + 1:02d}"
        else:
            new_event_id = "EVNT01"

        # Prepare the event entry for the database
        event_entry = {
            "event_id": new_event_id,
            "details": event_details,
            "event": event_data,
            "items": event_items,
            "form": event_summary,
            "association_name":association_name,
            "event_name":event_name
        }
        print("Event Entry to be inserted:", event_entry)
        
        # Insert data into the database
        event_collection.insert_one(event_entry)

        session["event_id"] = new_event_id

        return jsonify({"status": "success", "message": "Event submitted successfully!", "event_id": new_event_id}), 200

    except Exception as e:
        print("Error during event submission:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500


# Confirmation Page
@app.route('/confirm')
def confirm_page():
    event_id=session.get("event_id")
    return render_template('confirm.html',event_id=event_id)






@app.route('/view-preview', methods=['GET'])
def view_preview():
    # Retrieve event_id from session
    event_id = session.get("event_id")
    if not event_id:
        flash("No event ID found in session.")
        return redirect(url_for('event_page'))

    # Fetch event data from MongoDB
    event_datas = event_collection.find_one({"event_id": event_id})
    if not event_datas:
        flash("Event data not found.")
        return redirect(url_for('event_page'))

    try:
        # Fetch form data for rendering in event_preview.html
        association_name=event_datas.get("association_name")
        event_name=event_datas.get("event_name")

        form_data = event_datas.get("details", {})
        event_data = event_datas.get("form", {})
        items = event_datas.get("items", {})
        event_rounds=event_datas.get("event",{})

        # Generate and save multiple pages as PDFs
        pdf_filenames = []
        pdf_filepaths = []

        # Page 1
        html_content_page_1 = render_template(
            'event_start.html',
            event_id=event_id,
            association_name=association_name,
            event_name=event_name,
            event_datas=event_datas
        )
        pdf_output_page_1 = generate_pdf(html_content_page_1)
        pdf_filename_page_1 = generate_unique_filename("event_page1")
        pdf_filepath_page_1 = os.path.join('static', 'uploads', pdf_filename_page_1)
        save_pdf(pdf_output_page_1, pdf_filepath_page_1)
        pdf_filenames.append(pdf_filename_page_1)
        pdf_filepaths.append(pdf_filepath_page_1)

        # Page 2
        html_content_page_2 = render_template('page2.html')
        pdf_output_page_2 = generate_pdf(html_content_page_2)
        pdf_filename_page_2 = generate_unique_filename("event_page2")
        pdf_filepath_page_2 = os.path.join('static', 'uploads', pdf_filename_page_2)
        save_pdf(pdf_output_page_2, pdf_filepath_page_2)
        pdf_filenames.append(pdf_filename_page_2)
        pdf_filepaths.append(pdf_filepath_page_2)

        # Page 3 (Event preview page)
        html_content_page_3 = render_template(
            'event_preview.html',
            event_id=event_id,
            form_data=form_data,
            event_datas=event_datas
        )
        pdf_output_page_3 = generate_pdf(html_content_page_3)
        pdf_filename_page_3 = generate_unique_filename("event_page3")
        pdf_filepath_page_3 = os.path.join('static', 'uploads', pdf_filename_page_3)
        save_pdf(pdf_output_page_3, pdf_filepath_page_3)
        pdf_filenames.append(pdf_filename_page_3)
        pdf_filepaths.append(pdf_filepath_page_3)

        # Page 4 - Using PdfWriter (No template, programmatically generated)
        pdf_filename_page_4 = generate_unique_filename("event_page4")
        pdf_filepath_page_4 = os.path.join('static', 'uploads', pdf_filename_page_4)
        generate_and_save_pdf_page4(pdf_filepath_page_4, event_data)
        pdf_filenames.append(pdf_filename_page_4)
        pdf_filepaths.append(pdf_filepath_page_4)

        # Page 5 (Items Preview)
        html_content_page_5 = render_template(
            'items_preview.html',
            event_id=event_id,
            items=items,
            event_datas=event_datas
        )
        pdf_output_page_5 = generate_pdf(html_content_page_5)
        pdf_filename_page_5 = generate_unique_filename("event_page5")
        pdf_filepath_page_5 = os.path.join('static', 'uploads', pdf_filename_page_5)
        save_pdf(pdf_output_page_5, pdf_filepath_page_5)
        pdf_filenames.append(pdf_filename_page_5)
        pdf_filepaths.append(pdf_filepath_page_5)

        html_content_page_6 = render_template(
            'rounds_preview.html',
            event_id=event_id,
            event_rounds=event_rounds,
            event_datas=event_datas
        )
        pdf_output_page_6 = generate_pdf(html_content_page_6)
        pdf_filename_page_6 = generate_unique_filename("event_page6")
        pdf_filepath_page_6 = os.path.join('static', 'uploads', pdf_filename_page_6)
        save_pdf(pdf_output_page_6, pdf_filepath_page_6)
        pdf_filenames.append(pdf_filename_page_6)
        pdf_filepaths.append(pdf_filepath_page_6)

        # Merge the PDFs
        merged_pdf_filename = f"{event_id}_combined.pdf"
        merged_pdf_filepath = os.path.join('static', 'uploads', merged_pdf_filename)

        # Use PdfMerger to combine PDFs
        merger = PdfMerger()

        for pdf_path in pdf_filepaths:
            merger.append(pdf_path)

        # Write the merged PDF to the server
        merger.write(merged_pdf_filepath)
        merger.close()

        # Provide the merged PDF for download
        # flash(f"PDF successfully created and saved: {merged_pdf_filename}")

        # Clean up intermediate PDFs (delete them)
        for pdf_path in pdf_filepaths:
            os.remove(pdf_path)

        return send_from_directory(
            'static/uploads', 
            merged_pdf_filename, 
            as_attachment=True
        )

    except Exception as e:
        print(f"Error during preview: {e}")
        flash("An error occurred while generating the preview.")
        return redirect(url_for('event_page'))

def generate_unique_filename(prefix):
    """Generate a unique filename using a UUID and prefix."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4().hex[:6])  # Generates a short unique string
    return f"{prefix}_{timestamp}_{unique_id}.pdf"

def generate_pdf(html_content):
    """Generate PDF from HTML content using xhtml2pdf."""
    pdf_output = BytesIO()  # This creates an in-memory binary stream
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_output)
    if pisa_status.err:
        raise Exception("Error occurred while generating the PDF.")
    pdf_output.seek(0)  # Rewind the buffer to the beginning
    return pdf_output.read()

def save_pdf(pdf_output, filepath):
    """Save the generated PDF to the specified filepath."""
    with open(filepath, "wb") as pdf_file:
        pdf_file.write(pdf_output)

def generate_and_save_pdf_page4(filepath, event_data):
    """Generate a custom PDF for page 4 with aligned checkboxes and padding."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Margins and padding
    margin = 60
    padding = 20
    content_width = width - 2 * margin
    pdf.drawCentredString(width / 2, height - 30, "Event Details")

    # Top horizontal line
    pdf.line(margin, height - 40, width - margin, height - 40)

    # Vertical lines
    vertical_line_x = margin + padding
    pdf.line(margin, height - 40, margin, height - 520)
    pdf.line(width - margin, height - 40, width - margin, height - 520)

    y_pos = height - 60

    # Draw circular checkboxes for days
    label_x = vertical_line_x + 5
    checkbox_x = label_x + 100

    # Ensure alignment and spacing of days
    pdf.drawString(label_x, y_pos-10, "Day 1:")
    pdf.circle(checkbox_x - 55, y_pos - 5, 5, fill=1 if event_data.get("day") == "day_1" else 0)

    pdf.drawString(label_x + 120, y_pos-10, "Day 2:")
    pdf.circle(checkbox_x +65, y_pos-5 , 5, fill=1 if event_data.get("day")=="day_2" else 0)

    pdf.drawString(label_x + 240, y_pos-10, "Day 3:")
    pdf.circle(checkbox_x + 185, y_pos-6 , 5, fill=1 if event_data.get("day")=="day_3" else 0)

    pdf.drawString(label_x + 360, y_pos-10, "Two Days:")
    pdf.circle(checkbox_x + 328, y_pos-6, 5, fill=1 if event_data.get("day")=="two_days" else 0)
    if event_data.get("day")=="two_days":
            y_pos -= 20
            pdf.drawString(label_x+360, y_pos-10, f"Days: {event_data.get('two_days', 'N/A')}")


    # Horizontal line
    y_pos -= 30
    pdf.line(margin, y_pos, width - margin, y_pos)
    # Rounds
    y_pos -= 20
    pdf.drawString(label_x, y_pos-10, f"No of Rounds: {event_data.get('rounds', 'N/A')}")
    
    # Horizontal line

    # Participants
    y_pos -= 20
    pdf.drawString(label_x, y_pos-10, f"Expected no of Participants: {event_data.get('participants', 'N/A')}")
    y_pos -= 20
    pdf.drawString(label_x, y_pos-10, f"Duration of the event: {event_data.get('duration', 'N/A')}")

    # Horizontal line
    y_pos -= 30
    pdf.line(margin, y_pos, width - margin, y_pos)

    # Team information
    y_pos -= 20
    pdf.drawString(label_x+5, y_pos-7, "Individual:")
    pdf.circle(checkbox_x-30, y_pos-2, 5, fill=1 if event_data.get("participant_type")=="individual" else 0)

    pdf.drawString(label_x + 235, y_pos, "Team:")
    pdf.circle(checkbox_x + 190, y_pos+3 , 5, fill=1 if event_data.get("participant_type")=="team" else 0)

    y_pos -= 20
    pdf.drawString(label_x+235, y_pos, f"Min Size: {event_data.get('team_min', 'N/A')}")
    pdf.drawString(label_x + 235, y_pos-20, f"Max Size: {event_data.get('team_max', 'N/A')}")

    # Horizontal line
    y_pos -= 30
    pdf.line(margin, y_pos, width - margin, y_pos)
    center_x = width / 2  # Calculate the center of the page
    top_y = y_pos+70   # Y-position of the top horizontal line
    bottom_y = y_pos   # Y-position of the bottom horizontal line
    pdf.line(center_x, top_y, center_x, bottom_y)

    # Halls and slots
    y_pos -= 20
    pdf.drawString(label_x, y_pos-4, f"No of Halls Required: {event_data.get('halls_required', 'N/A')}")
    
    y_pos -= 20
    pdf.drawString(label_x, y_pos-4, f"Preferred Halls: {event_data.get('preferred_halls', 'N/A')}")
    y_pos -= 20
    pdf.drawString(label_x, y_pos-4, f"Reason: {event_data.get('hall_reason', 'N/A')}")

    # Horizontal line
    y_pos -= 30
    pdf.line(margin, y_pos, width - margin, y_pos)

    # Slots
    y_pos -= 20
    pdf.drawString(label_x, y_pos-5, "Slot Details:")
    y_pos -= 20
    pdf.drawString(label_x + 20, y_pos-5, "Slot 1: 9:30 to 12:30")
    pdf.circle(checkbox_x + 40, y_pos - 1, 5, fill=1 if event_data.get("slot")=="slot1"  else 0)

    y_pos -= 20
    pdf.drawString(label_x + 20, y_pos-5, "Slot 2: 1:30 to 4:30")
    pdf.circle(checkbox_x + 40, y_pos - 1, 5, fill=1 if event_data.get("slot")=="slot2"  else 0)

    y_pos -= 20
    pdf.drawString(label_x + 20, y_pos-5, "Full Day")
    pdf.circle(checkbox_x + 40, y_pos - 1, 5, fill=1 if event_data.get("slot")=="full_day"  else 0)

    # Horizontal line
    y_pos -= 30
    pdf.line(margin, y_pos, width - margin, y_pos)

    # Extension boxes
    y_pos -= 20
    pdf.drawString(label_x, y_pos-5, f"Extension Boxes: {event_data.get('extension_boxes', 'N/A')}")
    y_pos -= 20
    pdf.drawString(label_x, y_pos-5, f"Reason: {event_data.get('extension_reason', 'N/A')}")
    # Horizontal line
    y_pos -= 30
    pdf.line(margin, y_pos, width - margin, y_pos)

    # Signature fields
    y_pos -= 40
    pdf.drawString(label_x-25, y_pos, "Signature of the Secretary:")
    y_pos -= 30
    pdf.drawString(label_x-25, y_pos, "Signature of the Faculty Advisor:")

    # Save the generated PDF
    pdf.save()

    # Write the PDF to the specified filepath
    buffer.seek(0)
    with open(filepath, "wb") as f:
        f.write(buffer.read())
@app.route('/workshop-info', methods=['GET', 'POST'])
def workshop_info():
    if request.method == 'POST':
        # Collect event details and store in session
        workshop_details = {
            'association_name': request.form['association_name'],
            'workshop_name': request.form['workshop_name']
        }
        session['workshop_info'] = workshop_details
        return redirect(url_for('workshop_instruction'))

    return render_template('workshop_info.html')
@app.route('/workshop_instruction', methods=['GET', 'POST'])
def workshop_instruction():
    if request.method == 'POST':
        return redirect(url_for('workshop_detail'))
    return render_template('workshop_instruction.html')
@app.route('/workshop-detail', methods=['GET', 'POST'])
def workshop_detail():
    if request.method == 'POST':
        # Collect event details and store in session
        workshop_details = {
            'secretary_name': request.form['secretary_name'],
            'secretary_roll_number': request.form['secretary_roll_number'],
            'secretary_mobile': request.form['secretary_mobile'],
            'convenor_name': request.form['convenor_name'],
            'convenor_roll_number': request.form['convenor_roll_number'],
            'convenor_mobile': request.form['convenor_mobile'],
            'faculty_advisor_name': request.form['faculty_advisor_name'],
            'faculty_advisor_designation': request.form['faculty_advisor_designation'],
            'faculty_advisor_contact': request.form['faculty_advisor_contact'],
            'speaker_name': request.form['speaker_name'],
            'speaker_designation': request.form['speaker_designation'],
            'speaker_contact': request.form['speaker_contact']
        }
        session['workshop_details'] =workshop_details
        return redirect(url_for('workshop_page'))
    return render_template('workshop_detail.html')

@app.route('/workshop', methods=['GET', 'POST'])
def workshop_page():
    if request.method == 'POST':
        # Collect event data and store in session
        workshop_data = {
            'day_2': 'day_1' in request.form,
            'day_3': 'day_2' in request.form,
            'both_days': 'both_days' in request.form,
            'participants': request.form.get('participants'),
            'halls_required': request.form.get('halls_required'),
            'preferred_halls': request.form.get('preferred_halls'),
            'slot': request.form.get('slot'),
            'extension_boxes': request.form.get('extension_boxes'),
        }
        session['workshop_data'] = workshop_data
        return redirect(url_for('items_ws'))
    return render_template('workshop.html')
@app.route('/items_ws', methods=['GET', 'POST'])
def items_ws():
    
    if 'workshop_items' not in session:
        session['workshop_items'] = []

    if request.method == 'POST':
        # Collect item data from the form and store it in the session
        try:
            items_data = {
                "sno": request.form.get("sno"),
                "item_name": request.form.get("item_name"),
                "quantity": int(request.form.get("quantity")),
                "price_per_unit": float(request.form.get("price_per_unit")),
                "total_price": int(request.form.get("quantity")) * float(request.form.get("price_per_unit"))
            }

            # Validate required fields
            if not items_data["item_name"] or not items_data["quantity"]:
                flash("Item name and quantity are required.")
                return redirect(url_for('items_ws'))

            # Append item to session
            session['workshop_items'].append(items_data)
            flash("Item added successfully!")
            return redirect(url_for('workshop_summary'))
        except ValueError:
            flash("Please enter valid numeric values for quantity and price.")
            return redirect(url_for('items_ws'))

    return render_template('items_ws.html', workshop_items=session['workshop_items'])
@app.route('/workshop_summary', methods=['GET', 'POST'])
def workshop_summary():
    if request.method == 'POST':
        # Collect workshop general information
        workshop_name = request.form.get('workshop_name')
        description = request.form.get('workshop_description')
        prerequisites = request.form.get('workshop_prerequisites')
        
        # Initialize sessions list
        sessions = []

        # Get the number of sessions (from the input field in the HTML)
        session_count = int(request.form.get('session_count', 0))

        # Collect session details (session number, time, topic, and description)
        for i in range(session_count):
            sessions.append({
                "session_no": request.form.get(f'session_no_{i}'),
                "session_time": request.form.get(f'session_time_{i}'),
                "session_topic": request.form.get(f'session_topic_{i}'),
                "session_description": request.form.get(f'session_description_{i}')
            })

        # Store the workshop data in the session or database (depending on how you want to save it)
        session['workshop_summary'] = {
            "workshop_name": workshop_name,
            "description": description,
            "prerequisites": prerequisites,
            "sessions": sessions
        }

        # Redirect to the preview page (assuming a route named 'preview' exists)
        return redirect(url_for('preview_ws'))

    # If the method is GET, render the workshop form template
    return render_template('workshop_form.html')
@app.route('/preview_ws', methods=['GET'])
def preview_ws():
    try:
        # Retrieve workshop details, workshop data, workshop items, and workshop form data from session
        workshop_details = session.get('workshop_details', {})
        workshop_data = session.get('workshop_data', {})
        workshop_items = session.get('workshop_items', [])
        workshop_form_data = session.get('workshop_form_data', {})
        # if not workshop_items:
        #     flash("No items found.")
        # return redirect(url_for('items_ws_page')) 

        # Pass all the data to the template
        return render_template('preview_ws.html', 
                               workshop_details=workshop_details, 
                               workshop_data=workshop_data,
                               workshop_items=workshop_items,
                               workshop_form_data=workshop_form_data)
    except Exception:
        return jsonify({"status": "error", "message": "Error retrieving preview data"}), 500
@app.route('/submit_ws_event', methods=['POST'])
def submit_ws_event():
    try:
        # Get the request JSON data
        all_workshop_data = request.get_json()  # Correct method to get JSON data
        workshop_details = all_workshop_data.get('workshopDetails')
        workshop_data = all_workshop_data.get('workshopData')
        workshop_items = all_workshop_data.get('workshopItems')  # Correct field name should match
        workshop_summary = all_workshop_data.get('workshopFormData')
        association_name=all_workshop_data.get('association_name')
        workshop_name=all_workshop_data.get('workshop_name')

        # Log the received data to ensure it's correct
        print("Received event details:", workshop_details)
        print("Received event data:", workshop_data)
        print("Received event items:", workshop_items)  # Log items
        print("Received event summary:", workshop_summary)

        # Generate a new event ID based on the last event ID in the database
        existing_workshop = workshop_collection.find_one(sort=[("workshop_id", -1)])
        if existing_workshop and "workshop_id" in existing_workshop:
            last_workshop_num = int(existing_workshop["workshop_id"][4:])
            new_workshop_id = f"WKSP{last_workshop_num + 1:02d}"
        else:
            new_workshop_id = "WKSP01"

        # Prepare the event entry for the database
        workshop_entry = {
            "workshop_id": new_workshop_id,
            "details": workshop_details,
            "workshop": workshop_data,
            "items": workshop_items,
            "form": workshop_summary,
            "association_name":association_name,
            "workshop_name":workshop_name
        }
        print("Event Entry to be inserted:", workshop_entry)
        
        # Insert data into the database
        workshop_collection.insert_one(workshop_entry)

        session["workshop_id"] = new_workshop_id

        return jsonify({"status": "success", "message": "Event submitted successfully!", "workshop_id": new_workshop_id}), 200

    except Exception as e:
        print("Error during event submission:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/confirm_ws')
def confirm_ws_page():
    workshop_id=session.get("workshop_id")
    return render_template('confirm_ws.html',workshop_id=workshop_id)
@app.route('/view_preview_ws', methods=['GET'])
def view_preview_ws():
    try:
        # Retrieve event_id from session
        workshop_id = session.get("workshop_id")
        if not workshop_id:
            flash("No workshop ID found in session.")
            return redirect(url_for('workshop_page'))

        # Fetch event data from MongoDB
        workshop_datas = workshop_collection.find_one({"workshop_id": workshop_id})
        if not workshop_datas:
            flash("Workshop data not found.")
            return redirect(url_for('workshop_page'))

        # Fetch form data for rendering in event_preview.html
        association_name = workshop_datas.get("association_name")
        workshop_name = workshop_datas.get("workshop_name")

        form_data = workshop_datas.get("details", {})
        event_data = workshop_datas.get("form", {})
        items = workshop_datas.get("items", [])
        event_rounds = workshop_datas.get("workshop", {})

        # Generate and save multiple pages as PDFs
        pdf_filenames_ws = []
        pdf_filepaths_ws = []

        # Page 1: Workshop start page
        html_content_page_1 = render_template(
            'workshop_start.html',
            workshop_id=workshop_id,
            association_name=association_name,
            workshop_name=workshop_name,
            workshop_datas=workshop_datas
        )
        pdf_output_page_1 = generate_pdf(html_content_page_1)
        pdf_filename_page_1 = generate_unique_filename("workshop_page1")
        pdf_filepath_page_1 = os.path.join('static', 'uploads', pdf_filename_page_1)
        save_pdf(pdf_output_page_1, pdf_filepath_page_1)
        pdf_filenames_ws.append(pdf_filename_page_1)
        pdf_filepaths_ws.append(pdf_filepath_page_1)

        # Page 2: Event details page
        html_content_page_2 = render_template('page2_ws.html', event_data=event_data, items=items)
        pdf_output_page_2 = generate_pdf(html_content_page_2)
        pdf_filename_page_2 = generate_unique_filename("workshop_page2")
        pdf_filepath_page_2 = os.path.join('static', 'uploads', pdf_filename_page_2)
        save_pdf(pdf_output_page_2, pdf_filepath_page_2)
        pdf_filenames_ws.append(pdf_filename_page_2)
        pdf_filepaths_ws.append(pdf_filepath_page_2)

        # Page 3: Event preview page
        html_content_page_3 = render_template(
            'workshop_preview.html',
            workshop_id=workshop_id,
            form_data=form_data,
            # event_rounds=event_rounds,
            workshop_datas=workshop_datas
        )
        pdf_output_page_3 = generate_pdf(html_content_page_3)
        pdf_filename_page_3 = generate_unique_filename("workshop_page3")
        pdf_filepath_page_3 = os.path.join('static', 'uploads', pdf_filename_page_3)
        save_pdf(pdf_output_page_3, pdf_filepath_page_3)
        pdf_filenames_ws.append(pdf_filename_page_3)
        pdf_filepaths_ws.append(pdf_filepath_page_3)

        pdf_filename_page_4 = generate_unique_filename("workshop_page4")
        pdf_filepath_page_4 = os.path.join('static', 'uploads', pdf_filename_page_4)
        generate_pdf_ws(pdf_filepath_page_4, event_data)
        pdf_filenames_ws.append(pdf_filename_page_4)
        pdf_filepaths_ws.append(pdf_filepath_page_4)
        html_content_page_5 = render_template(
            'items_preview.html',
            workshop_id=workshop_id,
            items=items,
            workshop_datas=workshop_datas
        )
        pdf_output_page_5 = generate_pdf(html_content_page_5)
        pdf_filename_page_5 = generate_unique_filename("event_page5")
        pdf_filepath_page_5 = os.path.join('static', 'uploads', pdf_filename_page_5)
        save_pdf(pdf_output_page_5, pdf_filepath_page_5)
        pdf_filenames_ws.append(pdf_filename_page_5)
        pdf_filepaths_ws.append(pdf_filepath_page_5)

        html_content_page_6 = render_template(
            'session_preview.html',
            workshop_id=workshop_id,
            event_rounds=event_rounds,
            workshop_datas=workshop_datas
        )
        pdf_output_page_6 = generate_pdf(html_content_page_6)
        pdf_filename_page_6 = generate_unique_filename("event_page6")
        pdf_filepath_page_6 = os.path.join('static', 'uploads', pdf_filename_page_6)
        save_pdf(pdf_output_page_6, pdf_filepath_page_6)
        pdf_filenames_ws.append(pdf_filename_page_6)
        pdf_filepaths_ws.append(pdf_filepath_page_6)


        # Merge the PDFs
        merged_pdf_filename = f"{workshop_id}_combined.pdf"
        merged_pdf_filepath = os.path.join('static', 'uploads', merged_pdf_filename)

        # Use PdfMerger to combine PDFs
        merger = PdfMerger()
        for pdf_path in pdf_filepaths_ws:
            merger.append(pdf_path)

        # Write the merged PDF to the server
        merger.write(merged_pdf_filepath)
        merger.close()
        for pdf_path in pdf_filepaths_ws:
            os.remove(pdf_path)


        # Provide the merged PDF for download
        return send_from_directory(
            'static/uploads',
            merged_pdf_filename,
            as_attachment=True
        )

    except Exception as e:
        print(f"Error during preview: {e}")
        flash("An error occurred while generating the preview.")
        return redirect(url_for('workshop_page'))


def generate_pdf_ws(filepath, event_data):
    # Set up the canvas
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    # Starting coordinates
    start_x = 50
    start_y = height - 50
    line_height = 20
   

    # Outer border lines
    top_line_y = start_y + 20  # Position for the top horizontal line
    bottom_line_y = 50  # Position for the bottom horizontal line
    pdf.line(start_x, top_line_y, width - start_x, top_line_y)  # Top horizontal line
    pdf.line(start_x, top_line_y, start_x, bottom_line_y+182)  # Left vertical line
    pdf.line(width - start_x, top_line_y, width - start_x, bottom_line_y+182)  # Right vertical line

    # Title
    pdf.setFont("Helvetica-Bold", 12)
    start_y-=10
    pdf.drawString(start_x + 10, start_y, "DAY 2                    DAY 3                    BOTH DAYS")

    # Circles (checkboxes)
    pdf.circle(start_x + 62.5, start_y + 4, 5,fill=1 if event_data.get("day")=="day_2" else 0)
    pdf.circle(start_x + 160, start_y + 4, 5,fill=1 if event_data.get("day")=="day_3" else 0)
    pdf.circle(start_x + 300, start_y + 4, 5, fill=1 if event_data.get("day")=="both_days" else 0)

    # Table headers
    start_y -= 20
    pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line
    start_y -= 20
    pdf.setFont("Helvetica", 10)
    pdf.drawString(start_x + 10, start_y, f"EXPECTED NO. OF PARTICIPANTS:{event_data.get('participants','N/A')}")
    start_y -= 20
    pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line
    start_y -= line_height
    pdf.drawString(start_x + 10, start_y, f"PROPOSING FEES:{event_data.get('proposing_fee','N/A')}")
    pdf.drawString(start_x + 10, start_y - 20, f"Justification:{event_data.get('proposing_fees_justification','N/A')} ")

    # Line separator
    start_y -= 40
    pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line

    start_y -= 20
    pdf.drawString(start_x + 10, start_y, f"SPEAKER REMUNERATION (if any)(With justification):{event_data.get('speaker_remuneration','N/A')}")
    pdf.drawString(start_x + 10, start_y - 20, f"Justification:{event_data.get('speaker_remuneration_justification','N/A')} ")
    start_y -= 40
    pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line

    # Number of Halls/Labs
    start_y -= 30
    pdf.drawString(start_x + 10, start_y, f"NUMBER OF HALLS/LABS REQUIRED:{event_data.get('halls_required','N/A')}")
    start_y -= line_height
    pdf.drawString(start_x + 10, start_y, f"HALLS/LABS PREFERRED:{event_data.get('preferred_halls','N/A')}")
    start_y -= line_height
    pdf.drawString(start_x + 10, start_y, f"Reason:{event_data.get('preferred_hall_reason','N/A')}")
    start_y -= 50
    pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line

    # Duration of the Event
    start_y -= 20
    pdf.drawString(start_x + 10, start_y, f"DURATION OF THE EVENT IN HOURS:{event_data.get('duration')}")
    start_y -= 20
    pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line

    # Time Slots
    start_y -= 30
    pdf.drawString(start_x + 10, start_y, "START TO END TIME")
    pdf.drawString(start_x + 270, start_y, "SLOT 1          SLOT 2          FULL DAY")
    pdf.circle(start_x + 285, start_y-15, 5,fill=1 if event_data.get("slot")=="slot1" else 0)
    pdf.circle(start_x + 350, start_y-15, 5, fill=1 if event_data.get("slot")=="slot2" else 0)
    pdf.circle(start_x + 420, start_y-15, 5, fill=1 if event_data.get("slot")=="slot3" else 0)

    start_y -= line_height
    pdf.drawString(start_x + 10, start_y, "SLOT 1 : 9:30 TO 12:30")
    pdf.drawString(start_x + 10, start_y - line_height, "SLOT 2 : 1:30 TO 4:30")
    start_y -= 2 * line_height + 10  # Adjust spacing after time slots
    pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line
    center_x = width / 2  # Calculate the center of the page
    top_y = start_y+100   # Y-position of the top horizontal line
    bottom_y = start_y   # Y-position of the bottom horizontal line
    pdf.line(center_x, top_y, center_x, bottom_y)
    # Number Required
    start_y -= 30  # Space before the "NUMBER REQUIRED" section
    pdf.drawString(start_x + 10, start_y, f"NUMBER REQUIRED:{event_data.get('extension_boxes')}")
    pdf.drawString(start_x + 300, start_y, f"1. EXTENSION BOX :{event_data.get('extension_reason')}")
    start_y -= 30  # Space before the horizontal line
    pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line
    start_y -= 40
    pdf.drawString(start_x, start_y, "Signature of the Secretary:")
    start_y -= 30
    pdf.drawString(start_x,start_y, "Signature of the Faculty Advisor:")
    pdf.drawCentredString(width / 2, height - 20, "Workshop Details")

    # Finalize and save the PDF
    pdf.save()
    buffer.seek(0)
    with open(filepath, "wb") as f:
        f.write(buffer.read())



@app.route('/presentation-info', methods=['GET', 'POST'])
def presentation_info():
    if request.method == 'POST':
        # Collect presentation details and set 'presentation_name'
        presentation_details = {
            'association_name': request.form['association_name'],
            'presentation_name': request.form['presentation_name']
        }
        session['presentation_info'] = presentation_details
        return redirect(url_for('presentation_instructions'))

    return render_template('presentation_info.html')

@app.route('/presentation_instructions', methods=['GET', 'POST'])
def presentation_instructions():
    if request.method == 'POST':
        return redirect(url_for('presentation_detail'))
    return render_template('presentation_instruction.html')

@app.route('/presentation-detail', methods=['GET', 'POST'])
def presentation_detail():
    if request.method == 'POST':
        # Collect presentation details and store in session
        presentation_details = {
            'presentation_name': request.form['presentation_name'],
            'presenter_name': request.form['presenter_name'],
            'presenter_roll_number': request.form['presenter_roll_number'],
            'presenter_mobile': request.form['presenter_mobile'],
            'advisor_name': request.form['advisor_name'],
            'advisor_designation': request.form['advisor_designation'],
            'advisor_contact': request.form['advisor_contact'],
            'judge_name': request.form['judge_name'],
            'judge_designation': request.form['judge_designation'],
            'judge_contact': request.form['judge_contact']
        }
        session['presentation_details'] = presentation_details
        return redirect(url_for('presentation_page'))
    return render_template('presentation_detail.html')

@app.route('/presentation', methods=['GET', 'POST'])
def presentation_page():
    if request.method == 'POST':
        # Collect presentation data and store in session
        presentation_data = {
            'day': request.form.get('day'),
            'expected_participants': request.form.get('expected_participants'),
            'team_size_min': request.form.get('team_size_min'),
            'team_size_max': request.form.get('team_size_max'),
            'halls_required': request.form.get('halls_required'),
            'hall_reason': request.form.get('hall_reason'),
            'preferred_halls': request.form.get('preferred_halls'),
            'preferred_hall_reason': request.form.get('preferred_hall_reason'),
            'duration': request.form.get('duration'),
            'time_slot': request.form.get('time_slot'),
            'extension_boxes': request.form.get('extension_boxes'),
            'extension_box_reason': request.form.get('extension_box_reason'),
        }
        # Store the collected data in the session
        session['presentation_data'] = presentation_data

        # Redirect to a form preview or confirmation page
        return redirect(url_for('presentation_form'))

    # Render the form page
    return render_template('presentation.html')


@app.route('/presentation_form', methods=['GET', 'POST'])
def presentation_form():
    if request.method == 'POST':
        # Collect data from the form
        presentation_description = request.form.get('event_description')
        topics_and_theme = request.form.get('topics_and_theme')
        presentation_rules = request.form.get('event_rules')

        # Fetch the number of rounds dynamically
        round_no = int(request.form.get('round_no', 0))  # Default to 0 if not provided
        rounds = []

        # Extract round-wise details dynamically
        for i in range(1, round_no + 1):  # Loop based on the number of rounds entered
            rounds.append({
                "round_no": i,
                "time": request.form.get(f'round_{i}_time'),
                "description": request.form.get(f'round_{i}_description')
            })

        # Store data in the session
        session['presentation_form'] = {
            "presentation_description": presentation_description,
            "topics_and_theme": topics_and_theme,
            "presentation_rules": presentation_rules,
            "rounds": rounds
        }

        # Redirect to the preview page
        return redirect(url_for('presentation_preview'))

    # Render the form template
    return render_template('presentation_form.html')
@app.route('/presentation_preview', methods=['GET'])
def presentation_preview():
    try:
        # Retrieve presentation details, presentation data, presentation items, and presentation form data from session
        presentation_details = session.get('presentation_details', {})
        presentation_data = session.get('presentation_form', {})
        presentation_form_data = session.get('presentation_data', {})
        association_name=session.get('association_name')
        presentation_name=session.get('presentation_name')
    

        # Pass all the data to the template
        return render_template('presentation_preview.html', 
                               presentation_details=presentation_details, 
                               presentation_data=presentation_data,
                               presentation_form_data=presentation_form_data,association_name=association_name,presentation_name=presentation_name)
    
    except Exception:
        return jsonify({"status": "error", "message": "Error retrieving preview data"}), 500
    
@app.route('/submit_presentation', methods=['POST'])
def submit_presentation():
    
    try:
        # Get the request JSON data
        all_presentation_data = request.get_json() 
        print("Received Data:", all_presentation_data) # Correct method to get JSON data
        presentation_details = all_presentation_data.get('presentationDetails')
        presentation_data = all_presentation_data.get('presentationData')
        presentation_summary = all_presentation_data.get('presentationFormData')
        association_name = all_presentation_data.get('associationName')
        presentation_name = all_presentation_data.get('presentationName')

        # Log the received data to ensure it's correct
        print("Received presentation details:", presentation_details)
        print("Received presentation data:", presentation_data)
        print("Received presentation summary:", presentation_summary)
        print("Received presentation summary:", presentation_name)
        print("Received presentation summary:", association_name)


        # Generate a new event ID based on the last event ID in the database
        existing_event = presentation_collection.find_one(sort=[("presentation_id", -1)])
        if existing_event and "presentation_id" in existing_event:
            last_event_num = int(existing_event["presentation_id"][4:])
            presentation_id = f"PRPN{last_event_num + 1:02d}"
        else:
            presentation_id = "PRPN01"

        # Prepare the event entry for the database
        presentation_entry = {
            "presentation_id": presentation_id,
            "details": presentation_details,
            "presentation": presentation_data,
            "form": presentation_summary,
            "association_name":association_name,
            "presentation_name":presentation_name
        }
        print("Presentation Entry to be inserted:", presentation_entry)

        # Insert data into the database
        presentation_collection.insert_one(presentation_entry)

        session["presentation_id"] = presentation_id

        return jsonify({"status": "success", "message": "Presentation submitted successfully!", "presentation_id": presentation_id}), 200

    except Exception as e:
            print("Error during presentation submission:", str(e))
            return jsonify({"status": "error", "message": str(e)}), 500

# Confirmation Page
@app.route('/confirm2')
def confirm_page1():
    presentation_id=session.get("presentation_id")
    return render_template('confirm2.html',presentation_id=presentation_id)

@app.route('/view_preview_pp', methods=['GET'])
def view_preview_pp():
    try:
        # Retrieve event_id from session
        presentation_id = session.get("presentation_id")
        if not presentation_id:
            flash("No workshop ID found in session.")
            return redirect(url_for('presentation_page'))

        # Fetch event data from MongoDB
        presentation_datas= presentation_collection.find_one({"presentation_id": presentation_id})
        if not presentation_datas:
            flash("Presentation data not found.")
            return redirect(url_for('workshop_page'))

        # Fetch form data for rendering in event_preview.html
        association_name = presentation_datas.get("association_name")
        presentation_name = presentation_datas.get("presentation_name")

        form_data = presentation_datas.get("details", {})
        event_data = presentation_datas.get("form", {})
       
        presentation_rounds = presentation_datas.get("presentation", {})

        # Generate and save multiple pages as PDFs
        pdf_filenames_pp = []
        pdf_filepaths_pp = []

        # Page 1: Workshop start page
        html_content_page_1 = render_template(
            'presentation_start.html',
            presentation_id=presentation_id,
            association_name=association_name,
            presentation_name=presentation_name,
            presentation_datas=presentation_datas
        )
        pdf_output_page_1 = generate_pdf(html_content_page_1)
        pdf_filename_page_1 = generate_unique_filename("presentation_page1")
        pdf_filepath_page_1 = os.path.join('static', 'uploads', pdf_filename_page_1)
        save_pdf(pdf_output_page_1, pdf_filepath_page_1)
        pdf_filenames_pp.append(pdf_filename_page_1)
        pdf_filepaths_pp.append(pdf_filepath_page_1)

        # Page 2: Event details page
        html_content_page_2 = render_template('page2_ws.html',  )
        pdf_output_page_2 = generate_pdf(html_content_page_2)
        pdf_filename_page_2 = generate_unique_filename("presentation_page2")
        pdf_filepath_page_2 = os.path.join('static', 'uploads', pdf_filename_page_2)
        save_pdf(pdf_output_page_2, pdf_filepath_page_2)
        pdf_filenames_pp.append(pdf_filename_page_2)
        pdf_filepaths_pp.append(pdf_filepath_page_2)

        # Page 3: Event preview page
        html_content_page_3 = render_template(
            'presentation_page3.html',
            presentation_id=presentation_id,
            form_data=form_data,
            presentation_rounds=presentation_rounds,
            presentation_datas=presentation_datas
        )
        print(form_data)
        pdf_output_page_3 = generate_pdf(html_content_page_3)
        pdf_filename_page_3 = generate_unique_filename("presentation_page3")
        pdf_filepath_page_3 = os.path.join('static', 'uploads', pdf_filename_page_3)
        save_pdf(pdf_output_page_3, pdf_filepath_page_3)
        pdf_filenames_pp.append(pdf_filename_page_3)
        pdf_filepaths_pp.append(pdf_filepath_page_3)

        pdf_filename_page_4 = generate_unique_filename("presentation_page4")
        pdf_filepath_page_4 = os.path.join('static', 'uploads', pdf_filename_page_4)
        generate_pdf_content_pp(pdf_filepath_page_4, event_data)
        pdf_filenames_pp.append(pdf_filename_page_4)
        pdf_filepaths_pp.append(pdf_filepath_page_4)

        # html_content_page_5 = render_template(
        #     'items_preview.html',
        #     presentation_id=presentation_id,
        #     items=items,
        #     presentation_datas=presentation_datas
        # )
        # pdf_output_page_5 = generate_pdf(html_content_page_5)
        # pdf_filename_page_5 = generate_unique_filename("presentation_page5")
        # pdf_filepath_page_5 = os.path.join('static', 'uploads', pdf_filename_page_5)
        # save_pdf(pdf_output_page_5, pdf_filepath_page_5)
        # pdf_filenames_pp.append(pdf_filename_page_5)
        # pdf_filepaths_pp.append(pdf_filepath_page_5)

        html_content_page_6 = render_template(
            'presentation_last.html',
            presentation_id=presentation_id,
            presentation_rounds=presentation_rounds,
            presentation_datas=presentation_datas
        )
        print("Template rendered.")
        pdf_output_page_6 = generate_pdf(html_content_page_6)
        pdf_filename_page_6 = generate_unique_filename("presentation_page6")
        pdf_filepath_page_6 = os.path.join('static', 'uploads', pdf_filename_page_6)
        save_pdf(pdf_output_page_6, pdf_filepath_page_6)
        pdf_filenames_pp.append(pdf_filename_page_6)
        pdf_filepaths_pp.append(pdf_filepath_page_6)


        # Merge the PDFs
        merged_pdf_filename = f"{presentation_id}_combined.pdf"
        merged_pdf_filepath = os.path.join('static', 'uploads', merged_pdf_filename)

        # Use PdfMerger to combine PDFs
        merger = PdfMerger()
        for pdf_path in pdf_filepaths_pp:
            merger.append(pdf_path)

        # Write the merged PDF to the server
        merger.write(merged_pdf_filepath)
        merger.close()
        for pdf_path in pdf_filepaths_pp:
            os.remove(pdf_path)


        # Provide the merged PDF for download
        return send_from_directory(
            'static/uploads',
            merged_pdf_filename,
            as_attachment=True
        )

    except Exception as e:
        print(f"Error during preview: {e}")
        flash("An error occurred while generating the preview.")
        return redirect(url_for('workshop_page'))

def generate_pdf_content_pp(filepath,event_data):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Set margin for text placement
    margin = 60  # Left margin
    content_width = width - 2 * margin
    content_height = height - 2 * margin
    pdf.drawCentredString(width / 2, height - 30, "Presentation Details")
    # Draw a straightened horizontal line above the Day 1 contents
    pdf.line(margin - 20, height - 50, width - margin, height - 50)

    # Draw checkboxes for days (horizontally aligned)
    pdf.drawString(margin, height - 70, "Day 1:")
    # pdf.rect(margin + 40, height - 61, 10, 10, fill=1 if event_data.get("day")=="day_2" else 0)
    pdf.rect(margin + 41, height - 71, 10, 10,  fill=1 if event_data.get("day")=="day_2" else 0)

    pdf.drawString(margin + 80, height - 70, "Day 2:")
    # pdf.rect(margin + 130, height - 61, 10, 10, fill=1 if event_data.get("day")=="day_3" else 0)
    pdf.rect(margin + 120, height - 71, 10, 10, fill=1 if event_data.get("day")=="day_3" else 0 )

    pdf.drawString(margin + 170, height - 70, "Both Days:")
    # pdf.rect(margin + 250, height - 61, 10, 10, fill=1 if event_data.get("day")=="both_days" else 0)
    pdf.rect(margin + 239, height - 71, 10, 10,fill=1 if event_data.get("day")=="both_days" else 0 )
    # Draw a line after the checkboxes
    pdf.line(margin - 20, height - 80, width - margin, height - 80)

    # Draw vertical lines from the top horizontal line to the bottom horizontal line
    pdf.line(margin - 20, height - 50, margin - 20, height - 570)  # Left vertical line
    pdf.line(width - margin, height - 50, width - margin, height - 570)  # Right vertical line

    # Draw text fields for event data
    pdf.drawString(margin, height - 110, f"Expected No. of Participants:{event_data.get('expected_participants', '')} ")
    pdf.drawString(margin, height - 140, f"Team Size: Min:{event_data.get('team_size_min', '')}")

    # pdf.drawString(margin, height - 110, f"Expected No. of Participants: {event_data.get('participants', '')}")
    # pdf.drawString(margin, height - 140, f"Team Size: Min: {event_data.get('teamSizeMin', '')}, Max: {event_data.get('teamSizeMax', '')}")
    pdf.drawString(margin, height - 170, f"Team Size: Max:{event_data.get('team_size_max', '')}")
    # Draw a line after participants and team size
    pdf.line(margin - 20, height - 190, width - margin, height - 190)

    pdf.drawString(margin, height - 220, f"Number of Halls/Labs Required:{event_data.get('halls_required', '')} ")
    # pdf.drawString(margin, height - 170, f"Number of Halls/Labs Required: {event_data.get('hallsRequired', '')}")

    pdf.drawString(margin, height - 250, f"Halls/Labs Preferred:{event_data.get('preferred_halls', '')}")
    # pdf.drawString(margin + 20, height - 270, event_data.get("hallsPreferred", ""))

    pdf.drawString(margin, height - 280, f"Reason for Multiple Halls:{event_data.get('hall_reason', '')}")
    # pdf.drawString(margin + 20, height - 220, event_data.get("hallReason", ""))

    # Draw a line after halls and reasons
    # pdf.line(margin - 20, height - 230, width - margin, height - 230)


    # Draw a line after halls preferred
    pdf.line(margin - 20, height - 310, width - margin, height - 310)

    # Draw radio buttons for duration
    pdf.drawString(margin, height - 330, f"Duration of the Event in Hours:{event_data.get('duration', '')}")
    pdf.drawString(margin + 20, height - 350, "Slot 1: 9:30 to 12:30")
    pdf.circle(margin + 160, height - 345, 5,  fill=1 if event_data.get("time_slot") == "slot_1" else 0)
    pdf.drawString(margin + 20, height - 370, "Slot 2: 1:30 to 4:30")
    pdf.circle(margin + 160, height - 365, 5, fill=1 if event_data.get("time_slot") == "slot_2" else 0 )
    pdf.drawString(margin + 20, height - 390, "Full Day")
    pdf.circle(margin + 160, height - 385, 5, fill=1 if event_data.get("time_slot") == "full_day" else 0 )

    # pdf.drawString(margin, height - 300, "Duration of the Event in Hours:")
    # pdf.drawString(margin + 20, height - 320, "Slot 1: 9:30 to 12:30")
    # pdf.circle(margin + 160, height - 315, 5, fill=1 if event_data.get("duration") == "slot1" else 0)
    # pdf.drawString(margin + 20, height - 340, "Slot 2: 1:30 to 4:30")
    # pdf.circle(margin + 160, height - 335, 5, fill=1 if event_data.get("duration") == "slot2" else 0)
    # pdf.drawString(margin + 20, height - 360, "Full Day")
    # pdf.circle(margin + 160, height - 355, 5, fill=1 if event_data.get("duration") == "fullDay" else 0)
    # Draw a line after the duration radio buttons
    pdf.line(margin - 20, height - 410, width - margin, height - 410)

    pdf.drawString(margin, height - 440, f"Number Required:{event_data.get('extension_boxes', '')}")
    # pdf.drawString(margin, height - 390, f"Number Required: {event_data.get('numberRequired', '')}")
    pdf.drawString(margin, height - 470, f"Reason for Number:{event_data.get('extension_box_reason', '')}")
    # pdf.drawString(margin + 20, height - 440, event_data.get("numberReason", ""))

    # Draw a line after number and reason
    pdf.line(margin - 20, height - 500, width - margin, height - 500)

    pdf.drawString(margin, height - 525, f"Extension Box: ")
    # pdf.drawString(margin, height - 470, f"Extension Box: {event_data.get('extensionBox', '')}")

    # Draw a line after the extension box
    pdf.line(margin - 20, height - 570, width - margin, height - 570)

    # Draw signature fields
    pdf.drawString(margin-15, height - 610, f"Signature of the Secretary: ")
    pdf.drawString(margin-15, height - 640, f"Signature of the Faculty Advisor: ")

    pdf.save()
    buffer.seek(0)
    with open(filepath, "wb") as f:
        f.write(buffer.read())
@app.route('/event_search')
def event_search():
    return render_template('event_search.html')
@app.route('/workshop_search')
def workshop_search():
    return render_template('workshop_search.html')
@app.route('/workshop_display')
def workshop_display():
    return render_template('workshop_display.html')

@app.route('/search_event', methods=['GET'])
def search_event():
    search_id = request.args.get('id')  # Get the input from the search bar
    
    # If no search ID is provided
    if not search_id:
        return render_template('home.html', error="Please enter an ID to search.")
    
    # Check if the search ID starts with "WKSP" for workshop
    if search_id.startswith("WKSP"):
        # Fetch workshop data from the database
        workshop = workshop_collection.find_one({"workshop_id": search_id})
        if workshop:
            return render_template('workshop_search.html', workshop=workshop, error=None)
        else:
            return render_template('workshop_search.html', workshop=None, error="Workshop not found.")

    # Check if the search ID starts with "EVNT" for event
    elif search_id.startswith("EVNT"):
        # Fetch event data from the database
        event = event_collection.find_one({"event_id": search_id})
        if event:
            return render_template('event_search.html', event=event, error=None)
        else:
            return render_template('event_search.html', event=None, error="Event not found.")
        
    elif search_id.startswith("PPST"):
        # Fetch event data from the database
        presentation = presentation_collection.find_one({"presentation_id": search_id})
        if presentation:
            return render_template('presentation_search.html', presentation=presentation, error=None)
        else:
            return render_template('presentation_search.html', presentation=None, error="presentation not found.")
    
    # If the ID format is invalid
    return render_template('workshop_form.html', error="Invalid ID format. Please enter a valid Event ID or Workshop ID.")


@app.route('/download_pdf', methods=['GET'])
def download_pdf():
    # Retrieve event_id from session
    event_id = request.args.get('event_id')
    if not event_id:
        flash("No event ID found in session.")
        return redirect(url_for('event_page'))

    # Fetch event data from MongoDB
    event_datas = event_collection.find_one({"event_id": event_id})
    if not event_datas:
        flash("Event data not found.")
        return redirect(url_for('event_page'))

    try:
        # Fetch form data for rendering in event_preview.html
        association_name=event_datas.get("association_name")
        event_name=event_datas.get("event_name")

        form_data = event_datas.get("details", {})
        event_data = event_datas.get("form", {})
        items = event_datas.get("items", {})
        event_rounds=event_datas.get("event",{})

        # Generate and save multiple pages as PDFs
        pdf_filenames = []
        pdf_filepaths = []

        # Page 1
        html_content_page_1 = render_template(
            'event_start.html',
            event_id=event_id,
            association_name=association_name,
            event_name=event_name,
            event_datas=event_datas
        )
        pdf_output_page_1 = generate_pdf(html_content_page_1)
        pdf_filename_page_1 = generate_unique_filename("event_page1")
        pdf_filepath_page_1 = os.path.join('static', 'uploads', pdf_filename_page_1)
        save_pdf(pdf_output_page_1, pdf_filepath_page_1)
        pdf_filenames.append(pdf_filename_page_1)
        pdf_filepaths.append(pdf_filepath_page_1)

        # Page 2
        html_content_page_2 = render_template('page2.html')
        pdf_output_page_2 = generate_pdf(html_content_page_2)
        pdf_filename_page_2 = generate_unique_filename("event_page2")
        pdf_filepath_page_2 = os.path.join('static', 'uploads', pdf_filename_page_2)
        save_pdf(pdf_output_page_2, pdf_filepath_page_2)
        pdf_filenames.append(pdf_filename_page_2)
        pdf_filepaths.append(pdf_filepath_page_2)

        # Page 3 (Event preview page)
        html_content_page_3 = render_template(
            'event_preview.html',
            event_id=event_id,
            form_data=form_data,
            event_datas=event_datas
        )
        pdf_output_page_3 = generate_pdf(html_content_page_3)
        pdf_filename_page_3 = generate_unique_filename("event_page3")
        pdf_filepath_page_3 = os.path.join('static', 'uploads', pdf_filename_page_3)
        save_pdf(pdf_output_page_3, pdf_filepath_page_3)
        pdf_filenames.append(pdf_filename_page_3)
        pdf_filepaths.append(pdf_filepath_page_3)

        # Page 4 - Using PdfWriter (No template, programmatically generated)
        pdf_filename_page_4 = generate_unique_filename("event_page4")
        pdf_filepath_page_4 = os.path.join('static', 'uploads', pdf_filename_page_4)
        generate_and_save_pdf_page4(pdf_filepath_page_4, event_data)
        pdf_filenames.append(pdf_filename_page_4)
        pdf_filepaths.append(pdf_filepath_page_4)

        # Page 5 (Items Preview)
        html_content_page_5 = render_template(
            'items_preview.html',
            event_id=event_id,
            items=items,
            event_datas=event_datas
        )
        pdf_output_page_5 = generate_pdf(html_content_page_5)
        pdf_filename_page_5 = generate_unique_filename("event_page5")
        pdf_filepath_page_5 = os.path.join('static', 'uploads', pdf_filename_page_5)
        save_pdf(pdf_output_page_5, pdf_filepath_page_5)
        pdf_filenames.append(pdf_filename_page_5)
        pdf_filepaths.append(pdf_filepath_page_5)

        html_content_page_6 = render_template(
            'rounds_preview.html',
            event_id=event_id,
            event_rounds=event_rounds,
            event_datas=event_datas
        )
        pdf_output_page_6 = generate_pdf(html_content_page_6)
        pdf_filename_page_6 = generate_unique_filename("event_page6")
        pdf_filepath_page_6 = os.path.join('static', 'uploads', pdf_filename_page_6)
        save_pdf(pdf_output_page_6, pdf_filepath_page_6)
        pdf_filenames.append(pdf_filename_page_6)
        pdf_filepaths.append(pdf_filepath_page_6)

        # Merge the PDFs
        merged_pdf_filename = f"{event_id}_combined.pdf"
        merged_pdf_filepath = os.path.join('static', 'uploads', merged_pdf_filename)

        # Use PdfMerger to combine PDFs
        merger = PdfMerger()

        for pdf_path in pdf_filepaths:
            merger.append(pdf_path)

        # Write the merged PDF to the server
        merger.write(merged_pdf_filepath)
        merger.close()

        # Provide the merged PDF for download
        # flash(f"PDF successfully created and saved: {merged_pdf_filename}")

        # Clean up intermediate PDFs (delete them)
        for pdf_path in pdf_filepaths:
            os.remove(pdf_path)

        return send_from_directory(
            'static/uploads', 
            merged_pdf_filename, 
            as_attachment=True
        )

    except Exception as e:
        print(f"Error during preview: {e}")
        flash("An error occurred while generating the preview.")
        return redirect(url_for('event_page'))

def generate_unique_filename(prefix):
    """Generate a unique filename using a UUID and prefix."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4().hex[:6])  # Generates a short unique string
    return f"{prefix}_{timestamp}_{unique_id}.pdf"

def generate_pdf(html_content):
    """Generate PDF from HTML content using xhtml2pdf."""
    pdf_output = BytesIO()  # This creates an in-memory binary stream
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_output)
    if pisa_status.err:
        raise Exception("Error occurred while generating the PDF.")
    pdf_output.seek(0)  # Rewind the buffer to the beginning
    return pdf_output.read()

def save_pdf(pdf_output, filepath):
    """Save the generated PDF to the specified filepath."""
    with open(filepath, "wb") as pdf_file:
        pdf_file.write(pdf_output)

# def generate_and_save_pdf_page41(filepath, event_data):
#     """Generate a custom PDF for page 4 with aligned checkboxes and padding."""
#     buffer = BytesIO()
#     pdf = canvas.Canvas(buffer, pagesize=letter)
#     width, height = letter

#     # Margins and padding
#     margin = 60
#     padding = 20
#     content_width = width - 2 * margin

#     # Top horizontal line
#     pdf.line(margin, height - 40, width - margin, height - 40)

#     # Vertical lines
#     vertical_line_x = margin + padding
#     pdf.line(margin, height - 40, margin, height - 540)
#     pdf.line(width - margin, height - 40, width - margin, height - 540)

#     y_pos = height - 60

#     # Draw circular checkboxes for days
#     label_x = vertical_line_x + 5
#     checkbox_x = label_x + 100

#     # Ensure alignment and spacing of days
#     pdf.drawString(label_x, y_pos-10, "Day 1:")
#     pdf.circle(checkbox_x-55, y_pos-5 , 5, fill=1 if event_data.get("day_1") else 0)

#     pdf.drawString(label_x + 120, y_pos-10, "Day 2:")
#     pdf.circle(checkbox_x +65, y_pos-5 , 5, fill=1 if event_data.get("day_2") else 0)

#     pdf.drawString(label_x + 240, y_pos-10, "Day 3:")
#     pdf.circle(checkbox_x + 185, y_pos-6 , 5, fill=1 if event_data.get("day_3") else 0)

#     pdf.drawString(label_x + 360, y_pos-10, "Two Days:")
#     pdf.circle(checkbox_x + 328, y_pos-6, 5, fill=1 if event_data.get("two_days") else 0)

#     # Horizontal line
#     y_pos -= 30
#     pdf.line(margin, y_pos, width - margin, y_pos)

#     # Event type
#     y_pos -= 20
#     pdf.drawString(label_x, y_pos-10, "Technical Event:")
#     pdf.circle(checkbox_x, y_pos - 6, 5, fill=1 if event_data.get("technical_event") else 0)

#     pdf.drawString(label_x + 180, y_pos-10, "Non-Technical Event:")
#     pdf.circle(checkbox_x + 205, y_pos - 6, 5, fill=1 if event_data.get("non_technical_event") else 0)

#     # Horizontal line
#     y_pos -= 30
#     pdf.line(margin, y_pos, width - margin, y_pos)
#     center_x = width / 2  # Calculate the center of the page
#     top_y = y_pos+50   # Y-position of the top horizontal line
#     bottom_y = y_pos   # Y-position of the bottom horizontal line
#     pdf.line(center_x-80, top_y, center_x-80, bottom_y)
#     # Rounds
#     y_pos -= 20
#     pdf.drawString(label_x, y_pos-10, f"Rounds: {event_data.get('rounds', 'N/A')}")

#     # Horizontal line
#     y_pos -= 30
#     pdf.line(margin, y_pos, width - margin, y_pos)

#     # Participants
#     y_pos -= 20
#     pdf.drawString(label_x, y_pos-10, f"Participants: {event_data.get('participants', 'N/A')}")

#     # Horizontal line
#     y_pos -= 30
#     pdf.line(margin, y_pos, width - margin, y_pos)

#     # Team information
#     y_pos -= 20
#     pdf.drawString(label_x+5, y_pos-7, "Individual:")
#     pdf.circle(checkbox_x-30, y_pos-2, 5, fill=1 if event_data.get("individual") else 0)

#     pdf.drawString(label_x + 235, y_pos, "Team:")
#     pdf.circle(checkbox_x + 190, y_pos+3 , 5, fill=1 if event_data.get("team") else 0)

#     y_pos -= 20
#     pdf.drawString(label_x+235, y_pos, f"Min Size: {event_data.get('team_min', 'N/A')}")
#     pdf.drawString(label_x + 235, y_pos-20, f"Max Size: {event_data.get('team_max', 'N/A')}")

#     # Horizontal line
#     y_pos -= 30
#     pdf.line(margin, y_pos, width - margin, y_pos)
#     center_x = width / 2  # Calculate the center of the page
#     top_y = y_pos+70   # Y-position of the top horizontal line
#     bottom_y = y_pos   # Y-position of the bottom horizontal line
#     pdf.line(center_x, top_y, center_x, bottom_y)

#     # Halls and slots
#     y_pos -= 20
#     pdf.drawString(label_x, y_pos-4, f"Halls Required: {event_data.get('halls_required', 'N/A')}")
#     y_pos -= 20
#     pdf.drawString(label_x, y_pos-4, f"Preferred Halls: {event_data.get('preferred_halls', 'N/A')}")

#     # Horizontal line
#     y_pos -= 30
#     pdf.line(margin, y_pos, width - margin, y_pos)

#     # Slots
#     y_pos -= 20
#     pdf.drawString(label_x, y_pos-5, "Slot Details:")
#     y_pos -= 20
#     pdf.drawString(label_x + 20, y_pos-5, "Slot 1: 9:30 to 12:30")
#     pdf.circle(checkbox_x + 40, y_pos - 1, 5, fill=1 if event_data.get("slot1")  else 0)

#     y_pos -= 20
#     pdf.drawString(label_x + 20, y_pos-5, "Slot 2: 1:30 to 4:30")
#     pdf.circle(checkbox_x + 40, y_pos - 1, 5, fill=1 if event_data.get("slot2")  else 0)

#     y_pos -= 20
#     pdf.drawString(label_x + 20, y_pos-5, "Full Day")
#     pdf.circle(checkbox_x + 40, y_pos - 1, 5, fill=1 if event_data.get("full_day")  else 0)

#     # Horizontal line
#     y_pos -= 30
#     pdf.line(margin, y_pos, width - margin, y_pos)

#     # Extension boxes
#     y_pos -= 20
#     pdf.drawString(label_x, y_pos-5, f"Extension Boxes: {event_data.get('extension_boxes', 'N/A')}")

#     # Horizontal line
#     y_pos -= 30
#     pdf.line(margin, y_pos, width - margin, y_pos)

#     # Signature fields
#     y_pos -= 40
#     pdf.drawString(label_x-25, y_pos, "Signature of the Secretary:")
#     y_pos -= 30
#     pdf.drawString(label_x-25, y_pos, "Signature of the Faculty Advisor:")

#     # Save the generated PDF
#     pdf.save()

#     # Write the PDF to the specified filepath
#     buffer.seek(0)
#     with open(filepath, "wb") as f:
#         f.write(buffer.read())

@app.route('/download_pdf1', methods=['GET'])
def download_pdf1():
    try:
        # Retrieve event_id from session
        workshop_id = request.args.get("workshop_id")
        if not workshop_id:
            flash("No workshop ID found in session.")
            return redirect(url_for('workshop_page'))

        # Fetch event data from MongoDB
        workshop_datas = workshop_collection.find_one({"workshop_id": workshop_id})
        if not workshop_datas:
            flash("Workshop data not found.")
            return redirect(url_for('workshop_page'))

        # Fetch form data for rendering in event_preview.html
        association_name = workshop_datas.get("association_name")
        workshop_name = workshop_datas.get("workshop_name")

        form_data = workshop_datas.get("details", {})
        event_data = workshop_datas.get("form", {})
        items = workshop_datas.get("items", [])
        event_rounds = workshop_datas.get("workshop", {})

        # Generate and save multiple pages as PDFs
        pdf_filenames_ws = []
        pdf_filepaths_ws = []

        # Page 1: Workshop start page
        html_content_page_1 = render_template(
            'workshop_start.html',
            workshop_id=workshop_id,
            association_name=association_name,
            workshop_name=workshop_name,
            workshop_datas=workshop_datas
        )
        pdf_output_page_1 = generate_pdf(html_content_page_1)
        pdf_filename_page_1 = generate_unique_filename("workshop_page1")
        pdf_filepath_page_1 = os.path.join('static', 'uploads', pdf_filename_page_1)
        save_pdf(pdf_output_page_1, pdf_filepath_page_1)
        pdf_filenames_ws.append(pdf_filename_page_1)
        pdf_filepaths_ws.append(pdf_filepath_page_1)

        # Page 2: Event details page
        html_content_page_2 = render_template('page2_ws.html', event_data=event_data, items=items)
        pdf_output_page_2 = generate_pdf(html_content_page_2)
        pdf_filename_page_2 = generate_unique_filename("workshop_page2")
        pdf_filepath_page_2 = os.path.join('static', 'uploads', pdf_filename_page_2)
        save_pdf(pdf_output_page_2, pdf_filepath_page_2)
        pdf_filenames_ws.append(pdf_filename_page_2)
        pdf_filepaths_ws.append(pdf_filepath_page_2)

        # Page 3: Event preview page
        html_content_page_3 = render_template(
            'workshop_preview.html',
            workshop_id=workshop_id,
            form_data=form_data,
            # event_rounds=event_rounds,
            workshop_datas=workshop_datas
        )
        pdf_output_page_3 = generate_pdf(html_content_page_3)
        pdf_filename_page_3 = generate_unique_filename("workshop_page3")
        pdf_filepath_page_3 = os.path.join('static', 'uploads', pdf_filename_page_3)
        save_pdf(pdf_output_page_3, pdf_filepath_page_3)
        pdf_filenames_ws.append(pdf_filename_page_3)
        pdf_filepaths_ws.append(pdf_filepath_page_3)

        pdf_filename_page_4 = generate_unique_filename("workshop_page4")
        pdf_filepath_page_4 = os.path.join('static', 'uploads', pdf_filename_page_4)
        generate_pdf_ws(pdf_filepath_page_4, event_data)
        pdf_filenames_ws.append(pdf_filename_page_4)
        pdf_filepaths_ws.append(pdf_filepath_page_4)
        html_content_page_5 = render_template(
            'items_preview.html',
            workshop_id=workshop_id,
            items=items,
            workshop_datas=workshop_datas
        )
        pdf_output_page_5 = generate_pdf(html_content_page_5)
        pdf_filename_page_5 = generate_unique_filename("event_page5")
        pdf_filepath_page_5 = os.path.join('static', 'uploads', pdf_filename_page_5)
        save_pdf(pdf_output_page_5, pdf_filepath_page_5)
        pdf_filenames_ws.append(pdf_filename_page_5)
        pdf_filepaths_ws.append(pdf_filepath_page_5)

        html_content_page_6 = render_template(
            'session_preview.html',
            workshop_id=workshop_id,
            event_rounds=event_rounds,
            workshop_datas=workshop_datas
        )
        pdf_output_page_6 = generate_pdf(html_content_page_6)
        pdf_filename_page_6 = generate_unique_filename("event_page6")
        pdf_filepath_page_6 = os.path.join('static', 'uploads', pdf_filename_page_6)
        save_pdf(pdf_output_page_6, pdf_filepath_page_6)
        pdf_filenames_ws.append(pdf_filename_page_6)
        pdf_filepaths_ws.append(pdf_filepath_page_6)


        # Merge the PDFs
        merged_pdf_filename = f"{workshop_id}_combined.pdf"
        merged_pdf_filepath = os.path.join('static', 'uploads', merged_pdf_filename)

        # Use PdfMerger to combine PDFs
        merger = PdfMerger()
        for pdf_path in pdf_filepaths_ws:
            merger.append(pdf_path)

        # Write the merged PDF to the server
        merger.write(merged_pdf_filepath)
        merger.close()
        for pdf_path in pdf_filepaths_ws:
            os.remove(pdf_path)


        # Provide the merged PDF for download
        return send_from_directory(
            'static/uploads',
            merged_pdf_filename,
            as_attachment=True
        )

    except Exception as e:
        print(f"Error during preview: {e}")
        flash("An error occurred while generating the preview.")
        return redirect(url_for('workshop_page'))

# def generate_pdf_ws(filepath, event_data):
#     # Set up the canvas
#     buffer = BytesIO()
#     pdf = canvas.Canvas(buffer, pagesize=letter)
#     width, height = letter
#     # Starting coordinates
#     start_x = 50
#     start_y = height - 50
#     line_height = 20

#     # Outer border lines
#     top_line_y = start_y + 20  # Position for the top horizontal line
#     bottom_line_y = 50  # Position for the bottom horizontal line
#     pdf.line(start_x, top_line_y, width - start_x, top_line_y)  # Top horizontal line
#     pdf.line(start_x, top_line_y, start_x, bottom_line_y+182)  # Left vertical line
#     pdf.line(width - start_x, top_line_y, width - start_x, bottom_line_y+182)  # Right vertical line

#     # Title
#     pdf.setFont("Helvetica-Bold", 12)
#     start_y-=10
#     pdf.drawString(start_x + 10, start_y, "DAY 2                    DAY 3                    BOTH DAYS")

#     # Circles (checkboxes)
#     pdf.circle(start_x + 62.5, start_y + 4, 5,fill=1 if event_data.get("day")=="day_2" else 0)
#     pdf.circle(start_x + 160, start_y + 4, 5,fill=1 if event_data.get("day")=="day_3" else 0)
#     pdf.circle(start_x + 300, start_y + 4, 5, fill=1 if event_data.get("day")=="both_days" else 0)

#     # Table headers
#     start_y -= 20
#     pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line
#     start_y -= 20
#     pdf.setFont("Helvetica", 10)
#     pdf.drawString(start_x + 10, start_y, f"EXPECTED NO. OF PARTICIPANTS:{event_data.get('participants','N/A')}")
#     start_y -= 20
#     pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line
#     start_y -= line_height
#     pdf.drawString(start_x + 10, start_y, f"PROPOSING FEES:{event_data.get('proposing_fee','N/A')}")
#     pdf.drawString(start_x + 10, start_y - 20, f"Justification:{event_data.get('proposing_fees_justification','N/A')} ")

#     # Line separator
#     start_y -= 40
#     pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line

#     start_y -= 20
#     pdf.drawString(start_x + 10, start_y, f"SPEAKER REMUNERATION (if any)(With justification):{event_data.get('speaker_remuneration','N/A')}")
#     start_y -= 40
#     pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line

#     # Number of Halls/Labs
#     start_y -= 30
#     pdf.drawString(start_x + 10, start_y, f"NUMBER OF HALLS/LABS REQUIRED:{event_data.get('halls_required','N/A')}")
#     start_y -= line_height
#     pdf.drawString(start_x + 10, start_y, f"HALLS/LABS PREFERRED:{event_data.get('preferred_halls','N/A')}")
#     start_y -= line_height
#     pdf.drawString(start_x + 10, start_y, f"Reason:{event_data.get('preferred_hall_reason','N/A')}")
#     start_y -= 50
#     pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line

#     # Duration of the Event
#     start_y -= 20
#     pdf.drawString(start_x + 10, start_y, f"DURATION OF THE EVENT IN HOURS:{event_data.get('duration')}")
#     start_y -= 20
#     pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line

#     # Time Slots
#     start_y -= 30
#     pdf.drawString(start_x + 10, start_y, "START TO END TIME")
#     pdf.drawString(start_x + 270, start_y, "SLOT 1          SLOT 2          FULL DAY")
#     pdf.circle(start_x + 285, start_y-15, 5,fill=1 if event_data.get("slot")=="slot1" else 0)
#     pdf.circle(start_x + 350, start_y-15, 5, fill=1 if event_data.get("slot")=="slot2" else 0)
#     pdf.circle(start_x + 420, start_y-15, 5, fill=1 if event_data.get("slot")=="slot3" else 0)

#     start_y -= line_height
#     pdf.drawString(start_x + 10, start_y, "SLOT 1 : 9:30 TO 12:30")
#     pdf.drawString(start_x + 10, start_y - line_height, "SLOT 2 : 1:30 TO 4:30")
#     start_y -= 2 * line_height + 10  # Adjust spacing after time slots
#     pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line
#     center_x = width / 2  # Calculate the center of the page
#     top_y = start_y+100   # Y-position of the top horizontal line
#     bottom_y = start_y   # Y-position of the bottom horizontal line
#     pdf.line(center_x, top_y, center_x, bottom_y)
#     # Number Required
#     start_y -= 30  # Space before the "NUMBER REQUIRED" section
#     pdf.drawString(start_x + 10, start_y, f"NUMBER REQUIRED:{event_data.get('extension_boxes')}")
#     pdf.drawString(start_x + 300, start_y, f"1. EXTENSION BOX :{event_data.get('extension_reason')}")
#     start_y -= 30  # Space before the horizontal line
#     pdf.line(start_x, start_y, width - start_x, start_y)  # Horizontal line
#     start_y -= 40
#     pdf.drawString(start_x, start_y, "Signature of the Secretary:")
#     start_y -= 30
#     pdf.drawString(start_x,start_y, "Signature of the Faculty Advisor:")
#     pdf.drawCentredString(width / 2, height - 20, "Workshop Details")

#     # Finalize and save the PDF
#     pdf.save()
#     buffer.seek(0)
#     with open(filepath, "wb") as f:
#         f.write(buffer.read())
@app.route('/download_pdf2', methods=['GET'])
def download_pdf2():
    try:
        # Retrieve event_id from session
        presentation_id =request.args.get("presentation_id")
        if not presentation_id:
            flash("No workshop ID found in session.")
            return redirect(url_for('presentation_page'))

        # Fetch event data from MongoDB
        presentation_datas= presentation_collection.find_one({"presentation_id": presentation_id})
        if not presentation_datas:
            flash("Presentation data not found.")
            return redirect(url_for('workshop_page'))

        # Fetch form data for rendering in event_preview.html
        association_name = presentation_datas.get("association_name")
        presentation_name = presentation_datas.get("presentation_name")

        form_data = presentation_datas.get("details", {})
        event_data = presentation_datas.get("form", {})
       
        presentation_rounds = presentation_datas.get("presentation", {})

        # Generate and save multiple pages as PDFs
        pdf_filenames_pp = []
        pdf_filepaths_pp = []

        # Page 1: Workshop start page
        html_content_page_1 = render_template(
            'presentation_start.html',
            presentation_id=presentation_id,
            association_name=association_name,
            presentation_name=presentation_name,
            presentation_datas=presentation_datas
        )
        pdf_output_page_1 = generate_pdf(html_content_page_1)
        pdf_filename_page_1 = generate_unique_filename("presentation_page1")
        pdf_filepath_page_1 = os.path.join('static', 'uploads', pdf_filename_page_1)
        save_pdf(pdf_output_page_1, pdf_filepath_page_1)
        pdf_filenames_pp.append(pdf_filename_page_1)
        pdf_filepaths_pp.append(pdf_filepath_page_1)

        # Page 2: Event details page
        html_content_page_2 = render_template('page2_ws.html',  )
        pdf_output_page_2 = generate_pdf(html_content_page_2)
        pdf_filename_page_2 = generate_unique_filename("presentation_page2")
        pdf_filepath_page_2 = os.path.join('static', 'uploads', pdf_filename_page_2)
        save_pdf(pdf_output_page_2, pdf_filepath_page_2)
        pdf_filenames_pp.append(pdf_filename_page_2)
        pdf_filepaths_pp.append(pdf_filepath_page_2)

        # Page 3: Event preview page
        html_content_page_3 = render_template(
            'presentation_page3.html',
            presentation_id=presentation_id,
            form_data=form_data,
            presentation_rounds=presentation_rounds,
            presentation_datas=presentation_datas
        )
        print(form_data)
        pdf_output_page_3 = generate_pdf(html_content_page_3)
        pdf_filename_page_3 = generate_unique_filename("presentation_page3")
        pdf_filepath_page_3 = os.path.join('static', 'uploads', pdf_filename_page_3)
        save_pdf(pdf_output_page_3, pdf_filepath_page_3)
        pdf_filenames_pp.append(pdf_filename_page_3)
        pdf_filepaths_pp.append(pdf_filepath_page_3)

        pdf_filename_page_4 = generate_unique_filename("presentation_page4")
        pdf_filepath_page_4 = os.path.join('static', 'uploads', pdf_filename_page_4)
        generate_pdf_content_pp(pdf_filepath_page_4, event_data)
        pdf_filenames_pp.append(pdf_filename_page_4)
        pdf_filepaths_pp.append(pdf_filepath_page_4)

        # html_content_page_5 = render_template(
        #     'items_preview.html',
        #     presentation_id=presentation_id,
        #     items=items,
        #     presentation_datas=presentation_datas
        # )
        # pdf_output_page_5 = generate_pdf(html_content_page_5)
        # pdf_filename_page_5 = generate_unique_filename("presentation_page5")
        # pdf_filepath_page_5 = os.path.join('static', 'uploads', pdf_filename_page_5)
        # save_pdf(pdf_output_page_5, pdf_filepath_page_5)
        # pdf_filenames_pp.append(pdf_filename_page_5)
        # pdf_filepaths_pp.append(pdf_filepath_page_5)

        html_content_page_6 = render_template(
            'presentation_last.html',
            presentation_id=presentation_id,
            presentation_rounds=presentation_rounds,
            presentation_datas=presentation_datas
        )
        print("Template rendered.")
        pdf_output_page_6 = generate_pdf(html_content_page_6)
        pdf_filename_page_6 = generate_unique_filename("presentation_page6")
        pdf_filepath_page_6 = os.path.join('static', 'uploads', pdf_filename_page_6)
        save_pdf(pdf_output_page_6, pdf_filepath_page_6)
        pdf_filenames_pp.append(pdf_filename_page_6)
        pdf_filepaths_pp.append(pdf_filepath_page_6)


        # Merge the PDFs
        merged_pdf_filename = f"{presentation_id}_combined.pdf"
        merged_pdf_filepath = os.path.join('static', 'uploads', merged_pdf_filename)

        # Use PdfMerger to combine PDFs
        merger = PdfMerger()
        for pdf_path in pdf_filepaths_pp:
            merger.append(pdf_path)

        # Write the merged PDF to the server
        merger.write(merged_pdf_filepath)
        merger.close()
        for pdf_path in pdf_filepaths_pp:
            os.remove(pdf_path)


        # Provide the merged PDF for download
        return send_from_directory(
            'static/uploads',
            merged_pdf_filename,
            as_attachment=True
        )

    except Exception as e:
        print(f"Error during preview: {e}")
        flash("An error occurred while generating the preview.")
        return redirect(url_for('workshop_page'))

# def generate_pdf_content_pp(filepath,event_data):
#     buffer = BytesIO()
#     pdf = canvas.Canvas(buffer, pagesize=letter)
#     width, height = letter

#     # Set margin for text placement
#     margin = 60  # Left margin
#     content_width = width - 2 * margin
#     content_height = height - 2 * margin
#     pdf.drawCentredString(width / 2, height - 30, "Presentation Details")
#     # Draw a straightened horizontal line above the Day 1 contents
#     pdf.line(margin - 20, height - 50, width - margin, height - 50)

#     # Draw checkboxes for days (horizontally aligned)
#     pdf.drawString(margin, height - 70, "Day 1:")
#     # pdf.rect(margin + 40, height - 61, 10, 10, fill=1 if event_data.get("day")=="day_2" else 0)
#     pdf.rect(margin + 41, height - 71, 10, 10,  fill=1 if event_data.get("day")=="day_2" else 0)

#     pdf.drawString(margin + 80, height - 70, "Day 2:")
#     # pdf.rect(margin + 130, height - 61, 10, 10, fill=1 if event_data.get("day")=="day_3" else 0)
#     pdf.rect(margin + 120, height - 71, 10, 10, fill=1 if event_data.get("day")=="day_3" else 0 )

#     pdf.drawString(margin + 170, height - 70, "Both Days:")
#     # pdf.rect(margin + 250, height - 61, 10, 10, fill=1 if event_data.get("day")=="both_days" else 0)
#     pdf.rect(margin + 239, height - 71, 10, 10,fill=1 if event_data.get("day")=="both_days" else 0 )
#     # Draw a line after the checkboxes
#     pdf.line(margin - 20, height - 80, width - margin, height - 80)

#     # Draw vertical lines from the top horizontal line to the bottom horizontal line
#     pdf.line(margin - 20, height - 50, margin - 20, height - 570)  # Left vertical line
#     pdf.line(width - margin, height - 50, width - margin, height - 570)  # Right vertical line

#     # Draw text fields for event data
#     pdf.drawString(margin, height - 110, f"Expected No. of Participants:{event_data.get('expected_participants', '')} ")
#     pdf.drawString(margin, height - 140, f"Team Size: Min:{event_data.get('team_size_min', '')}")

#     # pdf.drawString(margin, height - 110, f"Expected No. of Participants: {event_data.get('participants', '')}")
#     # pdf.drawString(margin, height - 140, f"Team Size: Min: {event_data.get('teamSizeMin', '')}, Max: {event_data.get('teamSizeMax', '')}")
#     pdf.drawString(margin, height - 170, f"Team Size: Max:{event_data.get('team_size_max', '')}")
#     # Draw a line after participants and team size
#     pdf.line(margin - 20, height - 190, width - margin, height - 190)

#     pdf.drawString(margin, height - 220, f"Number of Halls/Labs Required:{event_data.get('halls_required', '')} ")
#     # pdf.drawString(margin, height - 170, f"Number of Halls/Labs Required: {event_data.get('hallsRequired', '')}")

#     pdf.drawString(margin, height - 250, f"Halls/Labs Preferred:{event_data.get('preferred_halls', '')}")
#     # pdf.drawString(margin + 20, height - 270, event_data.get("hallsPreferred", ""))

#     pdf.drawString(margin, height - 280, f"Reason for Multiple Halls:{event_data.get('hall_reason', '')}")
#     # pdf.drawString(margin + 20, height - 220, event_data.get("hallReason", ""))

#     # Draw a line after halls and reasons
#     # pdf.line(margin - 20, height - 230, width - margin, height - 230)


#     # Draw a line after halls preferred
#     pdf.line(margin - 20, height - 310, width - margin, height - 310)

#     # Draw radio buttons for duration
#     pdf.drawString(margin, height - 330, f"Duration of the Event in Hours:{event_data.get('duration', '')}")
#     pdf.drawString(margin + 20, height - 350, "Slot 1: 9:30 to 12:30")
#     pdf.circle(margin + 160, height - 345, 5,  fill=1 if event_data.get("time_slot") == "slot_1" else 0)
#     pdf.drawString(margin + 20, height - 370, "Slot 2: 1:30 to 4:30")
#     pdf.circle(margin + 160, height - 365, 5, fill=1 if event_data.get("time_slot") == "slot_2" else 0 )
#     pdf.drawString(margin + 20, height - 390, "Full Day")
#     pdf.circle(margin + 160, height - 385, 5, fill=1 if event_data.get("time_slot") == "full_day" else 0 )

#     # pdf.drawString(margin, height - 300, "Duration of the Event in Hours:")
#     # pdf.drawString(margin + 20, height - 320, "Slot 1: 9:30 to 12:30")
#     # pdf.circle(margin + 160, height - 315, 5, fill=1 if event_data.get("duration") == "slot1" else 0)
#     # pdf.drawString(margin + 20, height - 340, "Slot 2: 1:30 to 4:30")
#     # pdf.circle(margin + 160, height - 335, 5, fill=1 if event_data.get("duration") == "slot2" else 0)
#     # pdf.drawString(margin + 20, height - 360, "Full Day")
#     # pdf.circle(margin + 160, height - 355, 5, fill=1 if event_data.get("duration") == "fullDay" else 0)
#     # Draw a line after the duration radio buttons
#     pdf.line(margin - 20, height - 410, width - margin, height - 410)

#     pdf.drawString(margin, height - 440, f"Number Required:{event_data.get('extension_boxes', '')}")
#     # pdf.drawString(margin, height - 390, f"Number Required: {event_data.get('numberRequired', '')}")
#     pdf.drawString(margin, height - 470, f"Reason for Number:{event_data.get('extension_box_reason', '')}")
#     # pdf.drawString(margin + 20, height - 440, event_data.get("numberReason", ""))

#     # Draw a line after number and reason
#     pdf.line(margin - 20, height - 500, width - margin, height - 500)

#     pdf.drawString(margin, height - 525, f"Extension Box: ")
#     # pdf.drawString(margin, height - 470, f"Extension Box: {event_data.get('extensionBox', '')}")

#     # Draw a line after the extension box
#     pdf.line(margin - 20, height - 570, width - margin, height - 570)

#     # Draw signature fields
#     pdf.drawString(margin-15, height - 610, f"Signature of the Secretary: ")
#     pdf.drawString(margin-15, height - 640, f"Signature of the Faculty Advisor: ")

#     pdf.save()
#     buffer.seek(0)
#     with open(filepath, "wb") as f:
#         f.write(buffer.read())







if __name__ == '__main__':
    app.run(debug=True)

