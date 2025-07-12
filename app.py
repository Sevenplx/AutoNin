from flask import Flask, request, render_template, jsonify, session
from faster_whisper import WhisperModel
import re
import os
from werkzeug.utils import secure_filename
from flask_session import Session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_dev_key")
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

model = WhisperModel("tiny.en", compute_type="int8", download_root="/tmp")

def extract_fields(text):
    fields = session.get('fields', {})
    show_password_warning = False

    def clean_field(value):
        return value.replace("-", "").strip()

    name_match = re.search(r"(?:my name is|i am|i'm|this is)\s+(\w+)", text, re.IGNORECASE)
    if name_match:
        fields['name'] = name_match.group(1)

    # Improved and safer email logic
    def extract_fields(text):
    fields = session.get('fields', {})
    show_password_warning = False

    def clean_field(value):
        return value.replace("-", "").strip()

    # ===== NAME =====
    name_match = re.search(r"(?:my name is|i am|i'm|this is)\s+(\w+)", text, re.IGNORECASE)
    if name_match:
        fields['name'] = name_match.group(1)

    # ===== EMAIL =====
    def extract_email(text):
        text_lower = text.lower()

        # 1) If user said "my email", only look after that phrase
        start_idx = text_lower.find('my email')
        search_space = text_lower[start_idx:] if start_idx != -1 else text_lower

        # 2) Try to match spoken format: [words] at [words] .com
        m = re.search(
            r'\b([a-z0-9]+(?:\s+[a-z0-9]+)*)\s+at\s+([a-z0-9]+(?:\s+[a-z0-9]+)*)\s*\.?com\b',
            search_space
        )
        if m:
            local = m.group(1).replace(' ', '')
            domain = m.group(2).replace(' ', '')
            return f"{local}@{domain}.com"

        # 3) Fallback: any literal email in full text
        m2 = re.search(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
            text_lower
        )
        return m2.group(0) if m2 else None

    email = extract_email(text)
    if email:
        fields['email'] = email

    # flexible phone number extraction
    phone_match = re.search(
        r"(?:my\s+)?(?:phone\s+number\s+is|phone\s+is|contact\s+is|number\s+is|phone:)\s+(\+?[\d\s\-]+)",
        text,
        re.IGNORECASE
    )
    if phone_match:
        number = clean_field(phone_match.group(1))
        if len(re.sub(r"\D", "", number)) >= 10:  # ensure at least 10 digits
            fields['phone'] = number

    address_match = re.search(r"(?:my address is|address is)\s+(.+?)(?:[\.!?]|$)", text, re.IGNORECASE)
    if address_match:
        addr = address_match.group(1).replace(" slash ", "/").strip()
        fields['address'] = addr

    if re.search(r"password is\s+(.+?)(?:[\.!?]|$)", text, re.IGNORECASE):
        show_password_warning = True

    session['fields'] = fields
    return fields, show_password_warning

@app.route('/',methods=['GET','POST'])
def index():
    fields=session.get('fields',{})
    transcript=""
    if request.method=='POST':
        file=request.files.get('audiofile')
        if file and file.filename:
            fn=secure_filename(file.filename)
            path=os.path.join(app.config['UPLOAD_FOLDER'],fn)
            file.save(path)
            segments, info = model.transcribe(path)
            transcript = " ".join([seg.text for seg in segments])
            fields, warn=extract_fields(transcript)
            session['fields']=fields
    return render_template("index.html", fields=fields, transcript=transcript)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    file = request.files.get('audiofile')
    if not file:
        return jsonify({'error': 'No audio'}), 400
    fn = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], fn)
    file.save(path)

    segments, info = model.transcribe(path)
    text = " ".join([segment.text for segment in segments])

    fields, warn = extract_fields(text)
    session['fields'] = fields

    return jsonify({'text': text, 'fields': fields, 'passwordWarning': warn})

@app.route('/clear',methods=['POST'])
def clear():
    session.pop('fields',None)
    return ('', 204)

# No need for this below when deploying on Render(gunicorn will handel it):

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', debug=True)