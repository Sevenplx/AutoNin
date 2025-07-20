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

    # Normalize spoken email patterns
    spoken_email = text_lower
    spoken_email = re.sub(r"\s+at\s+", "@", spoken_email)
    spoken_email = re.sub(r"\s+dot\s+", ".", spoken_email)
    spoken_email = re.sub(r"dotcom\b", ".com", spoken_email)
    spoken_email = re.sub(r"dotorg\b", ".org", spoken_email)
    spoken_email = re.sub(r"dotedu\b", ".edu", spoken_email)
    # Handle common providers
    spoken_email = re.sub(r"gmail\s*dot\s*com", "gmail.com", spoken_email)
    spoken_email = re.sub(r"yahoo\s*dot\s*com", "yahoo.com", spoken_email)
    spoken_email = re.sub(r"outlook\s*dot\s*com", "outlook.com", spoken_email)
    spoken_email = re.sub(r"hotmail\s*dot\s*com", "hotmail.com", spoken_email)

    # Try to find a valid email
    m = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', spoken_email)
    if m:
        fields['email'] = m.group(0)
    else:
        # Handle broken-up usernames like "alex 383 at gmail.com"
        m2 = re.search(
            r'\b([a-z0-9]+)\s+([a-z0-9]+)\s*@\s*([a-z0-9.-]+)\s*\.\s*([a-z]{2,})\b',
            spoken_email
        )
        if m2:
            username = m2.group(1) + m2.group(2)
            domain = m2.group(3) + "." + m2.group(4)
            fields['email'] = f"{username}@{domain}"
        else:
            # fallback for "techatgmail.com"
            m3 = re.search(r'\b([a-z0-9._%+-]+)at([a-z0-9.-]+\.(?:com|org|edu|net))\b', spoken_email)
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