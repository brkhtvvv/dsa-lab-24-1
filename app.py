from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route('/number/', methods=['GET'])
def get_number():
    param = request.args.get('param', type=int)
    operations = ['sum', 'sub', 'mul', 'div']
    return jsonify({'number': param, 'operation': random.choice(operations)})

@app.route('/number/', methods=['POST'])
def post_number():
    data = request.get_json()
    param = data.get('param', 0)
    operations = ['sum', 'sub', 'mul', 'div']
    return jsonify({'number': param, 'operation': random.choice(operations)})

@app.route('/number/', methods=['DELETE'])
def delete_number():
    number = random.randint(1, 10)
    operations = ['sum', 'sub', 'mul', 'div']
    return jsonify({'number': number, 'operation': random.choice(operations)})

if __name__ == '__main__':
    app.run(debug=True)
