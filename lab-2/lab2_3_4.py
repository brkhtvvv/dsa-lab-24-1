import sys

# 1. Считываем массив из параметров командной строки
if len(sys.argv) < 2:
    print("Ошибка: Необходимо передать массив чисел в качестве аргументов командной строки.")
    sys.exit(1)

# Преобразуем аргументы командной строки в список целых чисел
try:
    array = list(map(int, sys.argv[1:]))
except ValueError:
    print("Ошибка: Все аргументы должны быть целыми числами.")
    sys.exit(1)

# 2. Находим максимальный элемент и его индекс
max_element = max(array)
max_index = array.index(max_element)
print(f"Максимальный элемент: {max_element}, его порядковый номер: {max_index}")

# 3. Находим все нечетные числа массива
odd_numbers = [x for x in array if x % 2 != 0]

if odd_numbers:
    # Выводим нечетные числа в порядке убывания
    odd_numbers.sort(reverse=True)
    print("Нечетные числа в порядке убывания:", " ".join(map(str, odd_numbers)))
else:
    print("Нечетных чисел нет.")


# python3 lab2_3_4.py 3 -1 4 -2 5