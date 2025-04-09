from flask import Flask, request
from markupsafe import escape


app = Flask(__name__)

@app.route('/')
def home():
    name = request.args.get("name", "World")
    safe_name = escape(name)  # 👈 Escaping user input manually
    return f"Hello, {safe_name}!"

if __name__ == '__main__':
    app.run(debug=True)
