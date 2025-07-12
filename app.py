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
    def extract_email(text):
        # 1) Lowercase & split into sentences
        text_lower = text.lower()
        sentences = re.split(r'[.?!]\s*', text_lower)

        target = None

        # Priority A: sentence containing "my email"
        for s in sentences:
            if 'my email' in s:
                target = s
                break

        # Priority B: first sentence starting with "[words] at [words] .com"
        if target is None:
            for s in sentences:
                if re.match(r'^\s*[\w\d]+(?:\s+[\w\d]+)*\s+at\s+[\w\d]+(?:\s+[\w\d]+)*\s*\.?com', s):
                    target = s
                    break

        if not target:
            return None  # no email found

        #  Normalize spoken tokens in target sentence
        norm = target
        norm = re.sub(r'\s+at\s+', '@', norm)
        norm = re.sub(r'\s+dot\s+', '.', norm)
        norm = re.sub(r'\s+underscore\s+', '_', norm)
        norm = re.sub(r'\s+dash\s+', '-', norm)

        # 4) Extract email with regex
        m = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', norm)
        return m.group(0).lower() if m else None

    # call the function and save email if found
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