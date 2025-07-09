# src/scripts/drainer_service.py
import logging
import pandas as pd
from sqlalchemy import func
from datetime import date, timedelta

from src.extensions import db, socketio
from src.models import StockClosing, AnomalousEvent

logger = logging.getLogger(__name__)

def _analyze_volume_spikes(days_history=90, std_dev_threshold=3.5):
    logger.info("[DrainerService] Iniciando análisis de picos de volumen...")
    events = []
    
    end_date = db.session.query(func.max(StockClosing.date)).scalar() or date.today()
    start_date = end_date - timedelta(days=days_history)

    query = db.session.query(
        StockClosing.nemo,
        StockClosing.date,
        StockClosing.previous_day_amount,
        StockClosing.previous_day_close_price
    ).filter(StockClosing.date.between(start_date, end_date)).order_by(StockClosing.nemo, StockClosing.date)
    
    df = pd.DataFrame(query.all())
    if df.empty:
        logger.warning("[DrainerService] No hay datos de cierre para analizar picos de volumen.")
        return []

    df['volume_ma'] = df.groupby('nemo')['previous_day_amount'].transform(lambda x: x.rolling(window=30, min_periods=10).mean())
    df['volume_std'] = df.groupby('nemo')['previous_day_amount'].transform(lambda x: x.rolling(window=30, min_periods=10).std())
    df['spike_threshold'] = df['volume_ma'] + (df['volume_std'] * std_dev_threshold)
    spikes_df = df[df['previous_day_amount'] > df['spike_threshold']].copy()
    
    for index, row in spikes_df.iterrows():
        future_date = row['date'] + timedelta(days=5)
        future_price_row = df[(df['nemo'] == row['nemo']) & (df['date'] >= future_date)].sort_values('date').iloc[:1]
        
        price_change = None
        if not future_price_row.empty and row['previous_day_close_price'] and row['previous_day_close_price'] > 0:
            future_price = future_price_row['previous_day_close_price'].values[0]
            price_change = ((future_price - row['previous_day_close_price']) / row['previous_day_close_price']) * 100

        avg_vol = row['volume_ma']
        spike_vol = row['previous_day_amount']
        times_avg = (spike_vol / avg_vol) if avg_vol and avg_vol > 0 else 0

        event = AnomalousEvent(
            nemo=row['nemo'],
            event_date=row['date'],
            event_type='Pico de Volumen',
            description=f"Volumen transado ({spike_vol or 0:,.0f} CLP) fue {times_avg:.1f} veces el promedio.",
            source='Análisis Interno de Volumen',
            price_change_pct=price_change
        )
        events.append(event)
        
    logger.info(f"[DrainerService] Se detectaron {len(events)} picos de volumen anómalos.")
    return events

def _simulate_insider_tracking():
    logger.info("[DrainerService] Simulando rastreo de insiders...")
    ipsa_stock = db.session.query(StockClosing).filter(StockClosing.belongs_to_ipsa == True).order_by(func.random()).first()
    if ipsa_stock:
        return AnomalousEvent(
            nemo=ipsa_stock.nemo, event_date=ipsa_stock.date - timedelta(days=3),
            event_type='Compra de Insider',
            description="Simulación: Detectada compra relevante de un director reportada a la CMF por 5,000 UF.",
            source='Simulador Scraper CMF', price_change_pct=None
        )
    return None

def _analyze_volume_spikes_with_pandas():
    """Analiza picos de volumen usando Pandas para mayor eficiencia."""
    try:
        # 1. Cargar los datos directamente en un DataFrame de Pandas
        # read_sql es muy eficiente para esto.
        query = StockClosing.query.statement
        df = pd.read_sql(query, db.session.bind)

        if df.empty:
            return []

        # 2. Asegurarse que los tipos de datos son correctos
        df['date'] = pd.to_datetime(df['date'])
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        # 3. Calcular la media móvil del volumen por cada acción (nemo)
        # Esto reemplaza bucles complejos con una sola operación vectorial.
        df['volume_MA_20D'] = df.groupby('nemo')['volume'].transform(
            lambda x: x.rolling(window=20, min_periods=5).mean()
        )

        # 4. Identificar picos donde el volumen actual es > 5 veces la media
        df['is_spike'] = df['volume'] > (df['volume_MA_20D'] * 5)
        
        spike_events = df[df['is_spike']].copy()

        # 5. Formatear los resultados para guardarlos en la BD
        events_to_save = []
        for _, row in spike_events.iterrows():
            events_to_save.append(AnomalousEvent(
                event_type='Volume Spike',
                nemo=row['nemo'],
                event_date=row['date'],
                description=f"Volumen de {row['volume']} fue >5x la media de 20 días ({row['volume_MA_20D']:.0f}).",
                severity='High'
            ))
        
        return events_to_save

    except Exception as e:
        logger.error(f"Error en análisis de volumen con Pandas: {e}", exc_info=True)
        return []

def run_drainer_analysis():
    try:
        AnomalousEvent.query.delete()
        db.session.commit()
        socketio.emit('drainer_progress', {'status': 'info', 'message': 'Resultados anteriores limpiados. Iniciando análisis...'})
        
        all_events = []
        volume_events = _analyze_volume_spikes()
        all_events.extend(volume_events)
        socketio.emit('drainer_progress', {'status': 'info', 'message': f'Análisis de volumen completo. {len(volume_events)} eventos encontrados.'})
        
        insider_event = _simulate_insider_tracking()
        if insider_event: all_events.append(insider_event)
        socketio.emit('drainer_progress', {'status': 'info', 'message': 'Rastreo de insiders (simulado) completo.'})
        
        if all_events:
            db.session.bulk_save_objects(all_events)
            db.session.commit()
            logger.info(f"✓ Guardados {len(all_events)} eventos anómalos en la base de datos.")
        
        socketio.emit('drainer_complete', {'status': 'success', 'message': f'Análisis finalizado. Total de eventos detectados: {len(all_events)}.'})
    except Exception as e:
        logger.error(f"Error crítico durante el análisis de drainers: {e}", exc_info=True)
        db.session.rollback()
        socketio.emit('drainer_complete', {'status': 'error', 'message': f'Error en el análisis: {e}'})