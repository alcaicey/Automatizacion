# tests/test_data_integrity.py
import pytest

def is_valid_stock_item(item):
    """
    Valida que un único diccionario de acción tenga la estructura y tipos de datos correctos.
    """
    if not isinstance(item, dict):
        return False
    
    required_keys = {
        "nemo": str,
        "precio": (int, float),
        "variacion": (int, float),
        "cierreAnterior": (int, float),
        "apertura": (int, float),
        "maximo": (int, float),
        "minimo": (int, float)
    }
    
    for key, expected_type in required_keys.items():
        if key not in item:
            return False
        if not isinstance(item[key], expected_type):
            return False
            
    return True

# Datos de prueba que simulan la respuesta de la API
mock_api_response = {
    "listaResult": [
        # Caso válido completo
        {
            "nemo": "SQM-B",
            "precio": 41500.50,
            "variacion": 1.25,
            "cierreAnterior": 41000.00,
            "apertura": 41200.00,
            "maximo": 41800.00,
            "minimo": 41100.00,
            "volumen": 100000
        },
        # Caso con un campo requerido faltante ("precio")
        {
            "nemo": "FALABELLA",
            "variacion": -0.5,
            "cierreAnterior": 2500.00,
            "apertura": 2510.00,
            "maximo": 2520.00,
            "minimo": 2490.00
        },
        # Caso con un tipo de dato incorrecto (precio es un string)
        {
            "nemo": "CMPC",
            "precio": "1500",  # Debería ser numérico
            "variacion": 0.0,
            "cierreAnterior": 1490.00,
            "apertura": 1495.00,
            "maximo": 1505.00,
            "minimo": 1490.00
        },
        # Otro caso válido
        {
            "nemo": "LTM",
            "precio": 8.5,
            "variacion": -2.1,
            "cierreAnterior": 8.7,
            "apertura": 8.6,
            "maximo": 8.8,
            "minimo": 8.4
        }
    ],
    "total": 4
}


def test_stock_data_structure():
    """
    GIVEN una respuesta simulada de la API de acciones
    WHEN se valida la estructura de cada elemento en la lista de resultados
    THEN solo los elementos que cumplen con el esquema (claves y tipos) deben ser válidos.
    """
    raw_data = mock_api_response.get("listaResult", [])
    
    # Aplicar el filtro de validación a cada item
    validated_data = [item for item in raw_data if is_valid_stock_item(item)]
    
    # Deberíamos encontrar solo 2 items válidos en nuestros datos de prueba
    assert len(validated_data) == 2, "La validación debería filtrar los items malformados."
    
    # Verificar que los items validados tienen los nemos correctos
    valid_nemos = [item["nemo"] for item in validated_data]
    assert "SQM-B" in valid_nemos
    assert "LTM" in valid_nemos
    
    # Verificar explícitamente la invalidez de los otros items
    assert not is_valid_stock_item(raw_data[1]), "Debe ser inválido por faltar el campo 'precio'."
    assert not is_valid_stock_item(raw_data[2]), "Debe ser inválido por tener 'precio' como string." 