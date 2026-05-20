# 📝 My notes about learning process
All notes about learning process and programming new tips 🫯

---

# 🕹️ Skills:
- .NET Frameworks
- MSSQL Server
- Version Control (Git)
- Vibe Coding)

---

# 👤 About me:

```JavaScript
bakhtovar = {
    name: "Bakhtovar",
    surname: "Ismatjonov",
    age: 19,
    gender: "male",
    isMarried: false 
};
```

---

# Notes:

## 1. Connect to Database:

```csharp
using System.Data.SqlClient;

class Program
{
    static void Main(string[] args)
    {
        string stringConnection = 
        "SERVER=.\\SQLEXPRESS;Database=test_db;Trusted_Connection=True;TrustServerCertificate=True";
        
        // Connecting
        SqlConnection connect = new SqlConnection(connectionString);
        
        // Checking for connection is true...
        try
        {
            Console.WriteLine("Checking...");
            connection.Open();
            Console.WriteLine("Connected!");
        }
        catch(Exception ex)
        {
            Console.WriteLine("Error: " + ex.Message);
        }
        finally
        {
            Console.ReadLine();
        }
    }
}
```
## 2. Multithreading
Creating and start a new thread
```csharp
Thread myThread = new Thread(Print);
myThread.Start();

void Print()
{
    Console.WriteLine("Hello Threads");
}

public delegate void ThreadStart();
```
Some useful properties and methods of Thread's class
```csharp
Thread.Name;  // Name of current thread
Thread.Sleep();  // Set up the timer for executing
```
Using method Sleep()
```csharp
using System.Threading;
 
for(int i = 0; i < 10; i++)
{
    Thread.Sleep(500);      // задержка выполнения на 500 миллисекунд
    Console.WriteLine(i);
}
```
Thread's synchronization with operator `lock`
```csharp
int x = 0;  // некоторый общий ресурс
Lock _lockObj = new(); // объект-заглушка для синхронизации доступа
// запускаем пять потоков
for (int i = 1; i < 6; i++)
{
    Thread myThread = new(Print);
    myThread.Name = $"Поток {i}";
    myThread.Start();
}
 
void Print()
{
    lock(_lockObj)  // начало критической секции
    {
        x = 1;
        for (int i = 1; i < 5; i++)
        {
            Console.WriteLine($"{Thread.CurrentThread.Name}: {x}");
            x++;
            Thread.Sleep(100);
        }
    }  // завершение критической секции
}
```