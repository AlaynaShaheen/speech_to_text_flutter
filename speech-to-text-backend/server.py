from flask import Flask, render_template
from flask_socketio import SocketIO
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, ResultReason, CancellationDetails
import os
import threading
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

speech_key = os.environ.get('AZURE_SPEECH_KEY', os.getenv("API_KEY"))
speech_region = os.environ.get('AZURE_SPEECH_REGION', os.getenv("REGION"))
speech_config = SpeechConfig(subscription=speech_key, region=speech_region)
speech_config.speech_recognition_language = "en-US"
recognizer = None
is_recognizing = False
lock = threading.Lock()

def recognition_callback(evt):
    with lock:
        if evt.result.reason == ResultReason.RecognizedSpeech:
            print(f"Recognized: {evt.result.text} at {datetime.now()}")
            socketio.emit('transcription', {
                'type': 'transcription',
                'text': evt.result.text,
                'append': True
            }, namespace='/')
        elif evt.result.reason == ResultReason.NoMatch:
            print("No speech could be recognized at {datetime.now()}")
        elif evt.result.reason == ResultReason.Canceled:
            cancellation_details = CancellationDetails(evt.result)
            print(f"Cancellation reason: {cancellation_details.reason} at {datetime.now()}")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f'SocketIO: Client connected at {datetime.now()}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'SocketIO: Client disconnected at {datetime.now()}')

@socketio.on('start_recognition')
def handle_start_recognition():
    global recognizer, is_recognizing
    print(f'Received start_recognition event at {datetime.now()}')
    with lock:
        if not is_recognizing:
            try:
                recognizer = SpeechRecognizer(speech_config=speech_config)
                recognizer.recognized.connect(recognition_callback)
                is_recognizing = True
                print('Speech recognizer initialized')
                socketio.emit('status', {
                    'type': 'status',
                    'isRecognizing': True,
                    'message': 'Speak into your microphone...'
                }, namespace='/')
                recognizer.start_continuous_recognition_async().get()
            except Exception as e:
                print(f"Error starting recognition: {e} at {datetime.now()}")
                socketio.emit('status', {
                    'type': 'status',
                    'isRecognizing': False,
                    'message': f"Error: {e}"
                }, namespace='/')
        else:
            print('Recognition already active, ignoring start_recognition at {datetime.now()}')

@socketio.on('stop_recognition')
def handle_stop_recognition():
    global recognizer, is_recognizing
    print(f'Received stop_recognition event at {datetime.now()}')
    with lock:
        if is_recognizing:
            is_recognizing = False
            if recognizer:
                try:
                    recognizer.stop_continuous_recognition_async()
                    threading.Timer(0.1, cleanup_recognizer).start()
                except Exception as e:
                    print(f"Error stopping recognition: {e} at {datetime.now()}")
                socketio.emit('status', {
                    'type': 'status',
                    'isRecognizing': False,
                    'message': 'Recognition stopped.'
                }, namespace='/')
                print('Session stopped at {datetime.now()}')
            else:
                socketio.emit('status', {
                    'type': 'status',
                    'isRecognizing': False,
                    'message': 'No recognizer active.'
                }, namespace='/')
        else:
            socketio.emit('status', {
                'type': 'status',
                'isRecognizing': False,
                'message': 'No active recognition to stop.'
            }, namespace='/')

def cleanup_recognizer():
    global recognizer
    with lock:
        if recognizer:
            recognizer = None
            print(f'Recognizer cleaned up at {datetime.now()}')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
# from flask import Flask, render_template
# from flask_socketio import SocketIO, emit
# from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, ResultReason
# import os
# import threading

# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app, cors_allowed_origins="*")

# speech_key = os.environ.get('AZURE_SPEECH_KEY', '71QggyM9ahBLmFUjevNggcajPipgMJHvVQpAHDHLE7c09aYEN7ycJQQJ99BFACGhslBXJ3w3AAAYACOGTJWz')
# speech_region = os.environ.get('AZURE_SPEECH_REGION', 'centralindia')
# speech_config = SpeechConfig(subscription=speech_key, region=speech_region)
# speech_config.speech_recognition_language = "en-US"
# recognizer = None
# is_recognizing = False

# def recognition_thread():
#     global recognizer, is_recognizing
#     while is_recognizing:
#         try:
#             result = recognizer.recognize_once_async().get()
#             if result.reason == ResultReason.RecognizedSpeech:
#                 print(f"Recognized: {result.text}")
#                 socketio.emit('transcription', {
#                     'type': 'transcription',
#                     'text': result.text,
#                     'append': True
#                 }, namespace='/')
#             elif result.reason == ResultReason.NoMatch:
#                 print("No speech could be recognized")
#             elif result.reason == ResultReason.Canceled:
#                 print(f"Cancellation reason: {result.cancellation_details.reason}")
#         except Exception as e:
#             print(f"Error in recognition: {e}")

# @app.route('/')
# def index():
#     return render_template('index.html')

# @socketio.on('connect')
# def handle_connect():
#     print('SocketIO: Client connected')

# @socketio.on('disconnect')
# def handle_disconnect():
#     print('SocketIO: Client disconnected')

# @socketio.on('start_recognition')
# def handle_start_recognition():
#     global recognizer, is_recognizing
#     print('Received start_recognition event')
#     if not is_recognizing:
#         try:
#             recognizer = SpeechRecognizer(speech_config=speech_config)
#             is_recognizing = True
#             print('Speech recognizer initialized')
#             socketio.emit('status', {
#                 'type': 'status',
#                 'isRecognizing': True,
#                 'message': 'Speak into your microphone...'
#             }, namespace='/')
#             threading.Thread(target=recognition_thread, daemon=True).start()
#         except Exception as e:
#             print(f"Error starting recognition: {e}")
#             socketio.emit('status', {
#                 'type': 'status',
#                 'isRecognizing': False,
#                 'message': f"Error: {e}"
#             }, namespace='/')

# @socketio.on('stop_recognition')
# def handle_stop_recognition():
#     global recognizer, is_recognizing
#     print('Received stop_recognition event')
#     if is_recognizing:
#         is_recognizing = False
#         if recognizer:
#             try:
#                 recognizer.stop_continuous_recognition_async().get()
#             except Exception as e:
#                 print(f"Error stopping recognition: {e}")
#             recognizer = None
#         print('Session stopped')

#         # ❌ Don't overwrite transcription
#         # ✅ Just send recognition status
#         socketio.emit('status', {
#             'type': 'status',
#             'isRecognizing': False,
#             'message': 'Recognition stopped.'
#         }, namespace='/')

#     else:
#         socketio.emit('status', {
#             'type': 'status',
#             'isRecognizing': False,
#             'message': 'No active recognition to stop.'
#         }, namespace='/')

# if __name__ == '__main__':
#     socketio.run(app, host='0.0.0.0', port=5000)
# from flask import Flask, render_template
# from flask_socketio import SocketIO, emit
# import azure.cognitiveservices.speech as speechsdk

# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'your-secret-key'
# socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent', logger=True, engineio_logger=True)

# subscription_key = "71QggyM9ahBLmFUjevNggcajPipgMJHvVQpAHDHLE7c09aYEN7ycJQQJ99BFACGhslBXJ3w3AAAYACOGTJWz"
# service_region = "centralindia"
# recognizer = None
# is_recognizing = False
# is_first_recognition = True

# @socketio.on('connect')
# def handle_connect():
#     print("SocketIO: Client connected")
#     emit('status', {'message': 'WebSocket connected'})

# @socketio.on('disconnect')
# def handle_disconnect():
#     print("SocketIO: Client disconnected")

# @socketio.on('start_recognition')
# def start_recognition():
#     global recognizer, is_recognizing, is_first_recognition
#     print("Received start_recognition event")
#     if is_recognizing:
#         emit('transcription', {'type': 'transcription', 'text': 'Recognition already in progress.'})
#         return
#     try:
#         speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=service_region)
#         speech_config.speech_recognition_language = "en-US"
#         audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
#         recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
#         print("Speech recognizer initialized")

#         def recognized_cb(evt):
#             global is_first_recognition
#             if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
#                 print(f"Recognized: {evt.result.text}")
#                 if is_first_recognition:
#                     socketio.emit('transcription', {'type': 'transcription', 'text': evt.result.text},broadcast=True)
#                     is_first_recognition = False
#                 else:
#                     socketio.emit('transcription', {'type': 'transcription', 'text': evt.result.text, 'append': True},broadcast=True)
#             elif evt.result.reason == speechsdk.ResultReason.NoMatch:
#                 print("No speech recognized")
#                 socketio.emit('transcription', {'type': 'transcription', 'text': 'No speech recognized.'})

#         def canceled_cb(evt):
#             global is_recognizing
#             print(f"Canceled: {evt.reason}, {evt.error_details}")
#             socketio.emit('transcription', {'type': 'transcription', 'text': f'Recognition canceled: {evt.reason}'})
#             if evt.reason == speechsdk.CancellationReason.Error:
#                 socketio.emit('transcription', {'type': 'transcription', 'text': f'Error: {evt.error_details}'})
#             if is_recognizing:
#                 stop_recognition()


#         recognizer.recognized.connect(recognized_cb)
#         recognizer.canceled.connect(canceled_cb)
#         recognizer.session_stopped.connect(lambda evt: print("Session stopped"))
#         recognizer.start_continuous_recognition_async().get()
#         print("Continuous recognition started")
#         is_recognizing = True
#         is_first_recognition = True
#         emit('status', {'type': 'status', 'isRecognizing': True, 'message': 'Speak into your microphone...'}, broadcast=True)
#     except Exception as e:
#         print(f"Error initializing recognition: {str(e)}")
#         emit('transcription', {'type': 'transcription', 'text': f'Error initializing recognition: {str(e)}'}, broadcast=True)
#         recognizer = None

# @socketio.on('stop_recognition')
# def stop_recognition():
#     global recognizer, is_recognizing
#     print("Received stop_recognition event")
#     if not is_recognizing or not recognizer:
#         emit('transcription', {'type': 'transcription', 'text': 'No active recognition to stop.'}, broadcast=True)
#         emit('status', {'type': 'status', 'isRecognizing': False}, broadcast=True)
#         return
#     try:
#         is_recognizing = False
#         recognizer.stop_continuous_recognition_async().get()
#         emit('transcription', {'type': 'transcription', 'text': 'Recognition stopped.'}, broadcast=True)
#         emit('status', {'type': 'status', 'isRecognizing': False}, broadcast=True)
#         recognizer = None
#     except Exception as e:
#         print(f"Error stopping recognition: {str(e)}")
#         emit('transcription', {'type': 'transcription', 'text': f'Error stopping recognition: {str(e)}'}, broadcast=True)
#         emit('status', {'type': 'status', 'isRecognizing': False}, broadcast=True)
#         recognizer = None

# @app.route('/')
# def index():
#     return render_template('index.html')

# if __name__ == '__main__':
#     from gevent import pywsgi
#     from geventwebsocket.handler import WebSocketHandler
#     server = pywsgi.WSGIServer(('0.0.0.0', 5000), app, handler_class=WebSocketHandler)
#     print("Starting server on http://0.0.0.0:5000")
#     server.serve_forever()         



















