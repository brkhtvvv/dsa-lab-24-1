from flask import Flask, request, jsonify

app = Flask(__name__)

RATES = {
    'EUR': 85.0,
    'USD': 80.0
}

@app.route('/rate', methods=['GET'])
def get_rate():
    currency = request.args.get('currency')
    if not currency or currency not in RATES:
        response = jsonify({
            'message': 'UNKNOWN CURRENCY'
        })
        response.status_code = 400
        return response
    try:
        rate = RATES[currency]
        return jsonify({
            'rate': rate
        }), 200
    except Exception:
        response = jsonify({
            'message': 'UNEXPECTED ERROR'
        })
        response.status_code = 500
        return response

if __name__ == '__main__':
    app.run(port=5000)
