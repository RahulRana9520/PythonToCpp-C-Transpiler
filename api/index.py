import sys
import os

# Ensure the api/ directory itself is on the path so 'converter' package is found
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify
from flask_cors import CORS
from converter.python_to_c import PythonToCConverter
from converter.python_to_cpp import PythonToCppConverter

app = Flask(__name__)
CORS(app)

# Initialize converters
c_converter = PythonToCConverter()
cpp_converter = PythonToCppConverter()

@app.route('/api/convert', methods=['POST'])
def convert():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        python_code = data.get('code', '')
        target = data.get('target', 'cpp')

        if not python_code.strip():
            return jsonify({
                'code': '',
                'warnings': [{'type': 'info', 'message': 'No input code provided'}],
                'ir': {'type': 'program', 'body': [], 'includes': []}
            })

        if target == 'c':
            converter = c_converter
        elif target == 'cpp':
            converter = cpp_converter
        else:
            return jsonify({'error': f'Invalid target language: {target}'}), 400

        result = converter.convert(python_code)

        return jsonify({
            'code': result['code'],
            'warnings': result['warnings'],
            'ir': result['ir']
        })

    except Exception as e:
        return jsonify({
            'code': f'// Error during transpilation\n// {str(e)}',
            'warnings': [{'type': 'error', 'message': f'Transpilation failed: {str(e)}'}],
            'ir': {'type': 'program', 'body': [], 'includes': []}
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

# Vercel calls the app object directly (WSGI)
# Do NOT include if __name__ == '__main__' block here
