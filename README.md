# AutoNin: Voice-to-Form AI Assistant

AutoNin is a smart AI-powered web assistant that allows users to fill out digital forms simply by **speaking**. It listens to your natural speech, transcribes it in real time, and intelligently fills in fields like your **name, email, phone number, and address**.

This project was designed to improve **accessibility**, save time, and showcase the power of **speech-to-text AI**, all built with **Python (Flask)** and **Faster-Whisper**.

---

## 🔗 Live Demo

**Try it out here** → [https://autonin-no00.onrender.com](https://autonin-no00.onrender.com)

> Works best on desktop or Chrome mobile.  
> Use your microphone or upload an audio file.

---

## > Screenshots

![Day/Night Theme](https://github.com/user-attachments/assets/6ed4bda9-bd70-4deb-85f2-5f78278c54fd)

![Audio visualizer](https://github.com/user-attachments/assets/9a99c294-fa49-4c11-b7ff-dd4a623bf91d)

![Modal Window](https://github.com/user-attachments/assets/3fee54b3-6cbb-4ab3-86cc-4131ac46568f)

[Day/Night Theme](https://github.com/user-attachments/assets/6ed4bda9-bd70-4deb-85f2-5f78278c54fd)

[Audio visualizer](https://github.com/user-attachments/assets/9a99c294-fa49-4c11-b7ff-dd4a623bf91d)

[Modal Window](https://github.com/user-attachments/assets/3fee54b3-6cbb-4ab3-86cc-4131ac46568f)

---
## > Features

-  **Voice-to-Form**: Speak naturally to fill the form.
-  **Upload Audio**: Supports uploading your own recordings.
-  **Real-Time AI**: Uses Faster-Whisper to transcribe voice input instantly.
-  **Smart Field Detection**: Detects name, email, phone, and address from voice.
-  **Privacy-Aware**: Warns if passwords are detected — does not auto-fill them.
-  **Responsive UI**: Optimized for mobile, tablet, and desktop.
-  **Interactive Feedback**: Audio visualizer, confetti, and fun UI elements, day/night theme.
-  **Built-in Tutorial**: Integrated YouTube tutorial + about, credits, contact modal.

---

## > Tech Stack

| Layer        | Technologies                               |
|--------------|--------------------------------------------|
| Frontend     | HTML, Tailwind CSS, JavaScript, Feather Icons |
| Backend      | Python (Flask), Flask-Session              |
| AI Engine    | Faster-Whisper (tiny.en model)             |
| Deployment   | Render.com                                 |

---

## > Project Structure
```plaintext 
AutoNin/
├── app.py # Flask backend
├── templates/
│ └── index.html # Main frontend with all UI logic
├── static/ # Assets like logo
├── uploads/ # Temporary audio files
├── requirements.txt # Python dependencies
└── README.md # Project overview
```

---

## > Getting Started (Local Setup)

### 1. Clone the repo

```bash
git clone https://github.com/Sevenplx/AutoNin.git
cd AutoNin
```
## Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```
## Install dependencies

```bash
pip install -r requirements.txt
```
 ## Run the app

 ```bash
python app.py
```
Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---
## > Use Cases
 For the elderly or disabled users — type-free interaction

-  Schools — quick student registration or surveys

-  Offices — hands-free data collection

-  Developers — experiment with voice-based AI UX

---
## > Credits
Developer: [Chemitha Sathsilu (Sevenplx)](https://github.com/Sevenplx)

AI Engine: Faster-Whisper

UI Framework: Tailwind CSS

Icons: Feather Icons

Hosting: [Render](render.com)

Special thanks to Dewmina Mandula and Iduwara Iluk [Rysera_community](rysera.com) for guidance and feedback.

---
## > Contributing
Contributions, bug reports, and feature suggestions are welcome!

-Fork the repo

-Make your changes

-Submit a pull request

## > Contact
Have questions, feedback, or want to collaborate?

Email: sathsiluchemitha@gmail.com

Instagram: [@sevenplx](www.instagram,com/sevenplx)
