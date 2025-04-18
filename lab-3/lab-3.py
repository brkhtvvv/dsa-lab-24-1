from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route('/number/', methods=['GET'])
def get_number():
    param = request.args.get('param')

    if not param:
        return jsonify({'error': "нужен параметр 'param'"}), 400

    try:
        param = float(param)
    except:
        return jsonify({'error': "'param' должен быть числом"}), 400

    rand = round(random.uniform(1, 100), 2)
    return jsonify({
        'число': param,
        'второе число': rand,
        'результат': round(param * rand, 2)
    })

@app.route('/number/', methods=['POST'])
def post_number():
    data = request.get_json()
    if not data or 'jsonParam' not in data:
        return jsonify({'error': "нужен параметр 'jsonParam'"}), 400

    try:
        value = float(data['jsonParam'])
    except:
        return jsonify({'error': "'jsonParam' должен быть числом"}), 400

    rand = round(random.uniform(1, 100), 2)
    op = random.choice(['sum', 'sub', 'mul', 'div'])

    if op == 'sum':
        result = rand + value
    elif op == 'sub':
        result = rand - value
    elif op == 'mul':
        result = rand * value
    else:
        if value == 0:
            return jsonify({'error': 'нельзя делить на ноль'}), 400
        result = rand / value

    return jsonify({
        'число': rand,
        'второе число': value,
        'операция': op,
        'результат': round(result, 2)
    })


@app.route('/number/', methods=['DELETE'])
def delete_number():
    a =  round(random.uniform(1, 100), 2)
    op = random.choice(['sum', 'sub', 'mul', 'div'])
    b =  round(random.uniform(1, 100), 2)

    if op == 'sum':
        result = a + b
    elif op == 'sub':
        result = a - b
    elif op == 'mul':
        result = a * b
    else:
        if b == 0:
            return jsonify({'error': 'нельзя делить на ноль'}), 400
        result = a / b
    return jsonify({
        'число': a,
        'второе число': b,
        'операция': op,
        'результат': round(result, 2),
    })

if __name__ == '__main__':
    app.run(debug=True)
