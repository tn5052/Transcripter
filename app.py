from flask import Flask, render_template, request, jsonify
import os
from VideoTranscriber import VideoTranscriber
import tempfile
import shutil

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize VideoTranscriber
transcriber = VideoTranscriber()

# Create a temporary directory
temp_dir = tempfile.mkdtemp()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    url = request.form.get('url')
    file = request.files.get('file')
    language = request.form.get('language', 'en')
    
    transcriber = VideoTranscriber(language=language)
    
    if url:
        try:
            transcript = transcriber.process_url(url)
            return jsonify({'status': 'success', 'transcript': transcript})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    elif file:
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No selected file'})
        
        # Ensure the temporary directory exists
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)
        try:
            transcript = transcriber.process_local_file(file_path)
            os.remove(file_path)
            return jsonify({'status': 'success', 'transcript': transcript})
        except Exception as e:
            os.remove(file_path)
            return jsonify({'status': 'error', 'message': str(e)})
    else:
        return jsonify({'status': 'error', 'message': 'No URL or file provided'})

@app.teardown_appcontext
def clean_temp_dir(exception=None):
    try:
        shutil.rmtree(temp_dir)
    except FileNotFoundError:
        pass

if __name__ == "__main__":
    app.run(debug=True)