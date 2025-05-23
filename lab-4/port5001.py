import psycopg2
from app import Flask, request, jsonify

app = Flask(__name__)

conn = psycopg2.connect(
    host="localhost",
    database="telegram_bot_db",
    user="postgres",
    password="postgres"
)

cur = conn.cursor()

cur.execute(
    "CREATE TABLE IF NOT EXISTS currencies ("
        "id INTEGER PRIMARY KEY,"
        "currency_name VARCHAR,"
        "rate NUMERIC)"
)

conn.commit()

cur.close()
conn.close()


@app.route('/load', methods=['POST'])
def load_currency():
    data = request.get_json()
    print("ПОЛУЧЕННЫЕ ДАННЫЕ:", data)

    name = data.get('currency_name')
    rate = data.get('rate')

    if not name or rate is None:
        return jsonify({"error": "Неверный формат запроса"}), 400

    try:
        rate = float(rate)
    except:
        return jsonify({"error": "Курс должен быть числом"}), 400

    conn = psycopg2.connect(
        host="localhost",
        database="telegram_bot_db",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM currencies WHERE UPPER(currency_name) = %s", (name.upper(),))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"error": "Такая валюта уже существует"}), 400

    cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM currencies")
    new_id = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO currencies (id, currency_name, rate) VALUES (%s, %s, %s)",
        (new_id, name.upper(), rate)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "OK", "currency": name.upper(), "rate": rate}), 200


@app.route('/update_currency', methods=['POST'])
def update_currency():
    data = request.get_json()
    name = data.get('currency_name')
    new_rate = data.get('rate')

    if not name or new_rate is None:
        return jsonify({"error": "Неверный формат запроса"}), 400

    conn = psycopg2.connect(
        host="localhost",
        database="telegram_bot_db",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()

   
    cur.execute("SELECT 1 FROM currencies WHERE UPPER(currency_name) = %s", (name.upper(),))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"error": "Валюта не найдена"}), 404

    
    cur.execute("UPDATE currencies SET rate = %s WHERE UPPER(currency_name) = %s", (new_rate, name.upper()))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "OK", "currency": name.upper(), "new_rate": new_rate}), 200


@app.route('/delete', methods=['POST'])
def delete_currency():
    data = request.get_json()
    name = data.get('currency_name')

    if not name:
        return jsonify({"error": "Не указано название валюты"}), 400

    conn = psycopg2.connect(
        host="localhost",
        database="telegram_bot_db",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()

    
    cur.execute("SELECT 1 FROM currencies WHERE UPPER(currency_name) = %s", (name.upper(),))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"error": "Валюта не найдена"}), 404

    
    cur.execute("DELETE FROM currencies WHERE UPPER(currency_name) = %s", (name.upper(),))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "OK", "deleted_currency": name.upper()}), 200

if __name__ == '__main__':
    app.run(port=5001)