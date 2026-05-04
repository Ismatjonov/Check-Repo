// Pluser.cpp : Этот файл содержит функцию "main". Здесь начинается и заканчивается выполнение программы.
//

#include <iostream>
#include <math.h>
using std::cin;
using std::cout;
using std::endl;

int main()
{
    std::cout << "Hello World!\n";
    int a;
    int b;
    cin >> a;
    cin >> b;
    int summa = a + b;
    cout << "Сумма: " << summa << endl;

    // Loop
    int i = 1;
    while (i < 10)
    {
        cout << i << " * " << i << " = " << i * i << endl;
        i++;
    }

    cout << "" << endl;

    for (int i = 1; i < 10; i++)
    {
        cout << i << " * " << i << " = " << i * i << endl;
    }

    return 0;
}