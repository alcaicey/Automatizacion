# src/utils/time_utils.py

import datetime
import pytz
import holidays
import logging

logger = logging.getLogger(__name__)

def get_fallback_market_time() -> datetime.datetime:
    """
    Calcula una hora de mercado de fallback basada en el último día hábil de cierre.
    - Si es un día hábil después de las 16:00, devuelve las 16:00 de hoy.
    - Si es un fin de semana, festivo, o antes de las 16:00, devuelve las 16:00 del último día hábil.
    """
    chile_tz = pytz.timezone('America/Santiago')
    chile_holidays = holidays.CL() # type: ignore
    now_chile = datetime.datetime.now(chile_tz)

    logger.info(f"Calculando hora de fallback. Hora actual en Chile: {now_chile.strftime('%Y-%m-%d %H:%M')}")

    def is_business_day(date_obj):
        """Verifica si una fecha es día hábil (lunes-viernes y no festivo)."""
        return date_obj.weekday() < 5 and date_obj not in chile_holidays

    # Caso 1: Hoy es día hábil y ya pasaron las 16:00 (hora de cierre)
    if is_business_day(now_chile.date()) and now_chile.hour >= 16:
        fallback_time = now_chile.replace(hour=16, minute=0, second=0, microsecond=0)
        logger.info(f"Día hábil post-cierre. Usando las 16:00 de hoy como fallback.")
        return fallback_time

    # Caso 2: Es fin de semana, festivo, o un día hábil antes del cierre.
    # Buscamos el último día hábil hacia atrás.
    last_business_day = now_chile.date() - datetime.timedelta(days=1)
    while not is_business_day(last_business_day):
        last_business_day -= datetime.timedelta(days=1)
    
    # Combinamos la fecha del último día hábil con la hora de cierre (16:00)
    fallback_time = chile_tz.localize(
        datetime.datetime.combine(last_business_day, datetime.time(16, 0))
    )
    
    logger.info("Fin de semana/festivo/pre-cierre. Usando cierre del último día hábil: {last_business_day.strftime('%Y-%m-%d')} a las 16:00.")
    return fallback_time

def is_market_open(current_time: datetime.time, open_time: datetime.time, close_time: datetime.time) -> bool:
    """
    Verifica si la hora actual está dentro del horario de mercado.
    Toma en cuenta que todas las horas deben tener la misma información de zona horaria.
    """
    # Verificación de días de semana (Lunes=0, Domingo=6)
    today = datetime.datetime.now(current_time.tzinfo).weekday()
    if today > 4: # Sábado o Domingo
        return False
        
    # Verificación de horario
    return open_time <= current_time < close_time