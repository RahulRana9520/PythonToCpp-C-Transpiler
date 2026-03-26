# TransPyC - Python to C/C++ Transpiler

A web-based transpiler that converts Python code to C or C++.

## Project Structure

```
TransPyC/
│
├── backend/
│   ├── app.py                      # Flask application
│   └── converter/
│       ├── __init__.py
│       ├── base_converter.py       # Base converter class
│       ├── python_to_c.py          # Python to C converter
│       ├── python_to_cpp.py        # Python to C++ converter
│       ├── ir_generator.py         # Intermediate representation generator
│       └── semantic_analyzer.py    # Semantic analysis
│
├── frontend/
│   ├── index.html                  # Main HTML page
│   ├── styles.css                  # Styles
│   └── app.js                      # Frontend JavaScript
│
└── requirements.txt                # Python dependencies
```

## Features

- Convert Python code to C or C++
- Support for functions, loops, conditionals, and basic I/O
- Real-time syntax checking
- Warning and error reporting
- Clean, modern web interface

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask backend:
```bash
cd backend
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Enter Python code in the left panel
2. Select target language (C or C++)
3. Click "Convert" button
4. View the converted code in the right panel

## Supported Python Features

- Function definitions
- Variables and assignments
- For loops (range-based)
- While loops
- If/elif/else conditionals
- Print statements
- Input statements (int, float, string)
- Basic arithmetic operations
- Comparison operators
- Comments

## Development

The transpiler works in three stages:

1. **Parsing**: Python code is parsed into an Intermediate Representation (IR)
2. **Semantic Analysis**: Type checking and validation
3. **Code Generation**: IR is converted to target language (C or C++)

## License

MIT License
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/REPLACE_WITH_PROJECT_ID) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/features/custom-domain#custom-domain)
