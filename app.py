from flask import Flask
import os

app = Flask(__name__, static_folder='src/static', static_url_path='/')

@app.route('/')
def index():
    return "Arabic Music AI is running!"

@app.route('/health')
def health_check():
    return {'status': 'healthy'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
