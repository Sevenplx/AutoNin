from flask import Flask, request, render_template, jsonify, session
import whisper
import re
import os
from werkzeug.utils import secure_filename
from flask_session import Session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

model = whisper.load_model("base")

def extract_fields(text):
    fields = session.get('fields', {})
    show_password_warning = False

    name_match = re.search(r"(?:my name is|i am|i'm|this is)\s+(\w+)", text, re.IGNORECASE)
    if name_match:
        fields['name'] = name_match.group(1)

    email_match = re.search(r"([\w.-]+)\s+at\s+([\w.-]+)(?:\s*(?:dot\s*com|\.com))", text, re.IGNORECASE)
    if email_match:
        local = email_match.group(1)
        domain = email_match.group(2)
        email = f"{local}@{domain}"
        if not email.endswith(".com"):
            email += ".com"
        fields['email'] = email.lower()
    else:
        raw_email = text.lower().replace(" at ", "@").replace(" dot ", ".").replace(" ", "").rstrip('.')
        email_clean = re.findall(r"[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}", raw_email)
        if email_clean:
            fields['email'] = email_clean[0].lower()

    phone_match = re.search(r"(?:phone number is|phone is)\s+(\+?[\d\s-]+)", text, re.IGNORECASE)
    if phone_match:
        fields['phone'] = phone_match.group(1).strip()

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
            res=model.transcribe(path)
            transcript=res.get('text','')
            fields, warn=extract_fields(transcript)
            session['fields']=fields
    return render_template("index.html", fields=fields, transcript=transcript)

@app.route('/transcribe',methods=['POST'])
def transcribe():
    file=request.files.get('audiofile')
    if not file: return jsonify({'error':'No audio'}),400
    fn=secure_filename(file.filename)
    path=os.path.join(app.config['UPLOAD_FOLDER'],fn)
    file.save(path)
    res=model.transcribe(path)
    text=res.get('text','')
    fields,warn=extract_fields(text)
    session['fields']=fields
    return jsonify({'text':text,'fields':fields,'passwordWarning':warn})

@app.route('/clear',methods=['POST'])
def clear():
    session.pop('fields',None)
    return ('', 204)

if __name__=='__main__':
    app.run(host='0.0.0.0', debug=True)
