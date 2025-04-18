import requests
import random

def convert_operation(op):
    return {
        'sum': '+', 'sub': '-', 'mul': '*', 'div': '/'
    }.get(op)

x = random.randint(1, 10)
resp_get = requests.get(f'http://127.0.0.1:5000/number/?param={x}').json()
print("GET:", resp_get)

n1 = resp_get.get('number')
op1 = convert_operation(resp_get.get('operation'))

y = random.randint(1, 10)
post_data = {'param': y}
resp_post = requests.post('http://127.0.0.1:5000/number/', json=post_data).json()
print("POST:", resp_post)

n2 = resp_post.get('number')
op2 = convert_operation(resp_post.get('operation'))

resp_delete = requests.delete('http://127.0.0.1:5000/number/').json()
print("DELETE:", resp_delete)

n3 = resp_delete.get('number')  
op3 = convert_operation(resp_delete.get('operation'))  

try:
    expr = f"{n1} {op1} {n2} {op2} {n3}"
    print(f"\nФормула: {expr}")
    print("Результат:", int(eval(expr)))  #eval для вычисления математического выражения, собранного из чисел и операторов
except Exception as e:
    print("Ошибка при вычислении выражения:", e)
