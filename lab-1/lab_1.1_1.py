a = float(input('Введите первое число: '))
b = float(input('Введите второе число: '))
c = float(input('Введите третье число: '))

if a <= b and a <= c:
    print( "Минимальное число: ", a)
elif b <= a and b <= c:
    print("Минимальное число: ", b)
else:
    print("Минимальное число: ", c)