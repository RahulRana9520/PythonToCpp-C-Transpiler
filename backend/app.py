from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from converter.python_to_c import PythonToCConverter
from converter.python_to_cpp import PythonToCppConverter

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# Initialize converters
c_converter = PythonToCConverter()
cpp_converter = PythonToCppConverter()

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/convert', methods=['POST'])
def convert():
    """
    Convert Python code to C or C++
    Request body: {
        "code": "Python code string",
        "target": "c" or "cpp"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No JSON data provided'
            }), 400
        
        python_code = data.get('code', '')
        target = data.get('target', 'cpp')
        
        if not python_code.strip():
            return jsonify({
                'code': '',
                'warnings': [{'type': 'info', 'message': 'No input code provided'}],
                'ir': {'type': 'program', 'body': [], 'includes': []}
            })
        
        # Select converter based on target
        if target == 'c':
            converter = c_converter
        elif target == 'cpp':
            converter = cpp_converter
        else:
            return jsonify({
                'error': f'Invalid target language: {target}'
            }), 400
        
        # Convert the code
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
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
