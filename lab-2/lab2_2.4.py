s = input("Введите строку: ")

# Подсчёт и замена английских 'a' и русских 'а'
count_replace = s.count('a') + s.count('а')
new_s = s.replace('a', 'o').replace('а', 'о')

print("Количество замен:", count_replace)
print("Изменённая строка:", new_s)
print("Количество символов в строке:", len(s))