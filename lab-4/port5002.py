import psycopg2
from app import Flask, request, jsonify

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="telegram_bot_db",
        user="postgres",
        password="postgres"
    )

@app.route('/currencies')
def get_currencies():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT currency_name, rate FROM currencies;")
            data = cur.fetchall()

    result = [{"currency_name": row[0], "rate": float(row[1])} for row in data]

    return jsonify(result)

@app.route('/convert')
def convert():
    currency = request.args.get('currency')
    amount = request.args.get('amount')

    if not currency or not amount:
        return jsonify({'error': 'Missing currency or amount'}), 400

    try:
        amount = float(amount)
    except ValueError:
        return jsonify({'error': 'Invalid amount format'}), 400

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT rate FROM currencies WHERE currency_name = %s;", (currency.upper(),))
            result = cur.fetchone()

    if result is None:
        return jsonify({'error': 'Currency not found'}), 404

    rate = float(result[0])
    converted = amount * rate

    return jsonify({
        'currency': currency.upper(),
        'rate': rate,
        'original_amount': amount,
        'converted_amount': round(converted, 2)
    })

if __name__ == '__main__':
    app.run(port=5002)
