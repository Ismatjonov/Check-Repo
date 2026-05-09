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
1. Connect to Database:

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