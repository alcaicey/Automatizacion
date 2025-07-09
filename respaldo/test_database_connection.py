import psycopg2
import pytest
import os

@pytest.mark.integration
def test_postgres_connection():
    """
    Intenta conectarse a la base de datos PostgreSQL usando variables de entorno
    o valores por defecto comunes. Falla si la conexión no se puede establecer.
    """
    conn = None
    try:
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            conn = psycopg2.connect(db_url)
        else:
            # Si DATABASE_URL no está, usa valores comunes de desarrollo
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", 5432),
                dbname=os.getenv("DB_NAME", "bolsa"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "postgres"),
            )
        
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        assert result[0] == 1, "La consulta de prueba a la base de datos no devolvió 1"
    
    except psycopg2.OperationalError as e:
        pytest.fail(f"No se pudo conectar a la base de datos: {e}")
        
    finally:
        if conn:
            conn.close() 