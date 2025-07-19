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

    # --- NAME extraction ---
    name_match = re.search(
        r"(?:my name is|i am|i'm|this is)\s+([A-Za-z][\w\.\- ]*?)(?=[.,!?]| and| and I|$)",
        text,
        re.IGNORECASE
    )
    if name_match:
        name = name_match.group(1).strip().rstrip(".!,?")
        fields['name'] = name

    # --- EMAIL extraction ---
    text_lower = text.lower()

    # 1) Normalize “.com/.org/.edu” → “ dot com ” etc.
    email_prefixes = [
        "my email is", "email is", "my email", "email:", "you can mail me at",
        "email me at", "mail me at"
    ]
    start_idx = -1
    for p in email_prefixes:
        idx = text_lower.find(p)
        if idx != -1:
            start_idx = idx + len(p)
            break

    # If prefix found, isolate substring for email detection without dotcom replacements
    if start_idx != -1:
        search_space = text_lower[start_idx:].strip()
    else:
        # Otherwise use whole text and replace dotcom etc for better matching
        search_space = text_lower
        search_space = re.sub(r'\.com\b', ' dot com ', search_space)
        search_space = re.sub(r'\.org\b', ' dot org ', search_space)
        search_space = re.sub(r'\.edu\b', ' dot edu ', search_space)
        search_space = re.sub(r'dotcom', 'dot com', search_space)
        search_space = re.sub(r'dotorg', 'dot org', search_space)
        search_space = re.sub(r'dotedu', 'dot edu', search_space)

    # 2) Spoken‑style extraction regex (same as before)
    m = re.search(
        r'\b([a-z0-9]+(?:[\s._-]*[a-z0-9]+)*)\s+at\s+([a-z0-9]+(?:[\s._-]*[a-z0-9]+)*)\s*(?:dot|\.|\s)\s*([a-z]{2,})\b',
        search_space
    )
    if m:
        local = re.sub(r'[\s._-]+', '', m.group(1))
        domain = re.sub(r'[\s._-]+', '', m.group(2))
        tld = m.group(3)
        fields['email'] = f"{local}@{domain}.{tld}"
    else:
        # 3) fallback literal email anywhere
        m2 = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text_lower)
        if m2:
            fields['email'] = m2.group(0)
        else:
            # 4) fallback for "techatgmail.com" (no @, but ends with gmail.com/yahoo.com/etc)
            m3 = re.search(r'\b([a-z0-9._%+-]+)at([a-z0-9.-]+\.(?:com|org|edu|net))\b', text_lower)
            if m3:
                fields['email'] = f"{m3.group(1)}@{m3.group(2)}"
    # --- PHONE ---
    phone_match = re.search(
        r"(?:my\s+)?(?:phone\s+number\s+is|phone\s+is|contact\s+is|number\s+is|phone:)\s+(\+?[\d\s\-]+)",
        text,
        re.IGNORECASE
    )
    if phone_match:
        number = clean_field(phone_match.group(1))
        if len(re.sub(r"\D", "", number)) >= 10:
            fields['phone'] = number

    # --- ADDRESS ---
    address_match = re.search(r"(?:my address is|address is)\s+(.+?)(?:[\.!?]|$)", text, re.IGNORECASE)
    if address_match:
        addr = address_match.group(1).replace(" slash ", "/").strip()
        fields['address'] = addr

    # --- PASSWORD Warning ---
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