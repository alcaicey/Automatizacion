
# Modelo de Datos

Este documento describe la estructura lógica y física de la base de datos de la aplicación.

## 1. Diagrama Entidad-Relación (ER)

El siguiente diagrama muestra las tablas principales de la base de datos y sus relaciones.

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
        int user_id FK
        string symbol
        float target_price
        string status
    }

    StockPrices {
        string symbol PK
        datetime timestamp PK
        float price
        float variation
    }

    Portfolio {
        int id PK
        string symbol
        int quantity
        float purchase_price
    }

    Dividends {
        int id PK
        string nemo
        date payment_date
        float value
    }

    StockFilters {
        int id PK
        text codes_json
    }

    LogEntries {
        int id PK
        string level
        text message
        datetime timestamp
    }

    Users ||--o{ Alerts : "tiene"
```

*Nota: Aunque no todas las relaciones están forzadas con claves foráneas a nivel de base de datos (ej. `Portfolio` a `Users`), lógicamente dependen de una configuración de usuario o global.*

## 2. Descripción de Tablas Principales y Definiciones (Pseudo-SQL)

A continuación se detalla el propósito y la estructura de las tablas más importantes.

### `stock_prices`
Almacena los datos de series temporales de los precios de las acciones. **Esta es una hypertable de TimescaleDB.**

```sql
CREATE TABLE stock_prices (
    symbol VARCHAR(50) NOT NULL,
    "timestamp" TIMESTAMPTZ NOT NULL,
    price FLOAT,
    variation FLOAT,
    buy_price FLOAT,
    sell_price FLOAT,
    amount BIGINT,
    traded_units BIGINT,
    currency VARCHAR(10),
    isin VARCHAR(50),
    green_bond VARCHAR(5),
    PRIMARY KEY (symbol, "timestamp")
);

-- Comando TimescaleDB ejecutado después de la creación
SELECT create_hypertable('stock_prices', 'timestamp');
```

### `users`
Guarda la información de los usuarios de la aplicación. (Actualmente parece una funcionalidad en desarrollo).

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL
);
```

### `credentials`
Almacena las credenciales para iniciar sesión en el sitio de la Bolsa de Santiago. En la implementación actual, suele haber un único registro global.

```sql
CREATE TABLE credentials (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL -- Se asume encriptación a nivel de aplicación si es necesario
);
```

### `portfolio`
Registra las acciones que posee el usuario, formando su cartera.

```sql
CREATE TABLE portfolio (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    quantity FLOAT NOT NULL,
    purchase_price FLOAT NOT NULL
);
```

### `alerts`
Configuración de alertas de precios para acciones específicas.

```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    symbol VARCHAR(50) NOT NULL,
    target_price FLOAT NOT NULL,
    condition VARCHAR(10) NOT NULL, -- "above" o "below"
    status VARCHAR(20) NOT NULL, -- "active", "triggered", etc.
    created_at TIMESTAMPTZ,
    triggered_at TIMESTAMPTZ
);
```

### `dividends`
Almacena información sobre los dividendos pagados por las acciones.

```sql
CREATE TABLE dividends (
    id SERIAL PRIMARY KEY,
    nemo VARCHAR(20) NOT NULL,
    description VARCHAR(255),
    limit_date DATE NOT NULL,
    payment_date DATE NOT NULL,
    currency VARCHAR(10),
    value FLOAT NOT NULL,
    UNIQUE (nemo, payment_date, description)
);
```

### Tablas de Configuración
Existen varias tablas para guardar las preferencias del usuario, como:
- **`stock_filters`**: Guarda los códigos de las acciones que el usuario desea filtrar.
- **`column_preferences`**, **`dividend_column_preferences`**, etc.: Almacenan las preferencias de columnas visibles en las diferentes tablas de la UI. Suelen contener un campo `TEXT` o `JSON` con la configuración.

## 3. Uso de TimescaleDB

La principal característica de la base de datos es el uso de la extensión **TimescaleDB** para la tabla `stock_prices`.

- **¿Qué es una Hypertable?**: Al convertir `stock_prices` en una hypertable, TimescaleDB la particiona automáticamente en segundo plano en trozos más pequeños (chunks), principalmente por la columna de tiempo (`timestamp`).
- **Ventajas**:
    - **Rendimiento en Inserciones**: Las inserciones de nuevos datos de precios son mucho más rápidas porque solo afectan al "chunk" más reciente.
    - **Consultas de Tiempo Eficientes**: Las consultas que filtran por rangos de tiempo (ej. "mostrar los precios de la última semana") son extremadamente rápidas, ya que TimescaleDB solo necesita leer los chunks relevantes en lugar de escanear toda la tabla.
    - **Gestión de Datos Simplificada**: Facilita políticas de retención de datos (ej. borrar automáticamente datos con más de X años) y la compresión de datos antiguos.

La creación de la hypertable se realiza automáticamente después de que SQLAlchemy crea la tabla, gracias a un listener de eventos de DDL definido en el modelo `StockPrice`. 