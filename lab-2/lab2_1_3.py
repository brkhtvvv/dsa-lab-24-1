m = float(input("Введите вещественное число m: "))

# Используем цикл for для вычисления и вывода членов последовательности
for i in range(1, 11):  # range(1, 11) дает числа от 1 до 10
    result = i * m
    print(f"{i} * {m} = {result}")