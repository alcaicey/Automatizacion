# Diagrama de Base de Datos

```mermaid
erDiagram
    Users {
        int id PK
        string username
        string email
    }
    Credentials {
        int id PK
        string username
        string password
    }
    Alerts {
        int id PK
        string symbol
        float target_price
    }
    StockPrices {
        string symbol PK
        datetime timestamp PK
        float price
    }
    StockClosings {
        date date PK
        string nemo PK
        float previous_day_close_price
    }
    Portfolio {
        int id PK
        string symbol
        int quantity
    }
    Dividends {
        int id PK
        string nemo
        date payment_date
    }
    StockFilters {
        int id PK
        text codes_json
    }
    AnomalousEvent {
        int id PK
        string nemo
        date event_date
        string event_type
    }
    AdvancedKPI {
        int id PK
        string nemo
        date date
        json source_details
    }
    PromptConfig {
        int id PK
        string api_provider
        string api_key
    }
    KpiSelection {
        int id PK
        string kpi_name
        boolean is_selected
    }
    PortfolioColumnPreference {
        int id PK
        text columns_json
    }
    ClosingColumnPreference {
        int id PK
        text columns_json
    }
    DividendColumnPreference {
        int id PK
        text columns_json
    }
    KpiColumnPreference {
        int id PK
        text columns_json
    }

    Users ||--o{ Alerts : "configura"
    StockClosings ||--o{ AdvancedKPI : "tiene"
```
