# Инициализация переменных
numbers = []  # Список для хранения введенных чисел
sum_of_numbers = 0  # Переменная для хранения суммы чисел
count_of_numbers = 0  # Переменная для хранения количества чисел

# Считываем числа с клавиатуры
print("Введите последовательность целых чисел (для завершения ввода введите 'm'):")
while True:
    user_input = input("Введите число (или 'm' для завершения): ")
    if user_input == 'm':  
        break
    try:
        number = int(user_input)  # Преобразуем введенное значение в целое число
        numbers.append(number)  # Добавляем число в список
        sum_of_numbers += number  # Увеличиваем сумму
        count_of_numbers += 1  # Увеличиваем счетчик чисел
    except ValueError:
        print("Ошибка: введено не число. Попробуйте снова.")

# Выводим результаты
if count_of_numbers > 0:
    print(f"Сумма всех чисел последовательности: {sum_of_numbers}")
    print(f"Количество всех чисел последовательности: {count_of_numbers}")
else:
    print("Последовательность пуста.")