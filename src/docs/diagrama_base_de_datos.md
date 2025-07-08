# Diagrama de base de datos

```mermaid
erDiagram
    STOCK_PRICES {
        string symbol PK
        datetime timestamp PK
        float price
        float variation
    }
    CREDENTIALS {
        int id PK
        string username
        string password
    }
    USERS {
        int id PK
        string username
        string email
    }
    COLUMN_PREFERENCES {
        int id PK
        text columns_json
    }
    STOCK_FILTERS {
        int id PK
        text codes_json
        boolean all
    }
    LAST_UPDATE {
        int id PK
        datetime timestamp
    }
    LOG_ENTRIES {
        int id PK
        string level
        text message
        string action
        text stack
        datetime timestamp
    }
```
