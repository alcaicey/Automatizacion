# src/routes/api/bot_routes.py

import asyncio
import json
import logging
import os
import threading
import time
from flask import jsonify, current_app, request

from sqlalchemy.dialects.postgresql import insert
from src.routes.api import api_bp
from src.models import StockFilter, AdvancedKPI, KpiSelection, StockClosing

from src.scripts.bolsa_service import run_bolsa_bot, is_bot_running as is_async_bot_running
from src.scripts import dividend_service, closing_service, ai_financial_service
from src.scripts.bot_page_manager import get_page
from src.extensions import socketio, db

logger = logging.getLogger(__name__)
_sync_bot_running_lock = threading.Lock() 

# Constante para el mensaje de error del loop de eventos
BOT_EVENT_LOOP_NOT_RUNNING_ERROR = "El loop de eventos del bot no está corriendo."

def is_bot_busy():
    """Comprueba tanto el lock síncrono como el estado del loop asíncrono."""
    return _sync_bot_running_lock.locked() or is_async_bot_running()

async def _fetch_and_process_kpis(nemos: list[str]) -> list[dict]:
    """
    Obtiene KPIs para una lista de nemotécnicos en paralelo utilizando un ejecutor
    y devuelve una lista de datos listos para la actualización de la base de datos.
    """
    loop = asyncio.get_running_loop()
    
    # Crea un futuro para cada nemo para preservar la asociación
    futures = {
        loop.run_in_executor(None, ai_financial_service.get_advanced_kpis, nemo): nemo
        for nemo in nemos
    }
    
    upsert_data = []
    for future in asyncio.as_completed(futures):
        nemo = futures[future]
        try:
            kpi_data = await future
            if kpi_data and not kpi_data.get('error'):
                # Adaptar la nueva estructura de respuesta de la IA
                processed_data = {
                    'nemo': nemo,
                    'roe': kpi_data.get('kpis', {}).get('roe'),
                    'beta': kpi_data.get('kpis', {}).get('beta'),
                    'debt_to_equity': kpi_data.get('kpis', {}).get('debt_to_equity'),
                    'analyst_recommendation': kpi_data.get('analyst_recommendation'),
                    'source': kpi_data.get('main_source'),
                    # Extraer detalles y guardarlos como JSON
                    'source_details': {k: v.get('source') for k, v in kpi_data.get('details', {}).items()},
                    'calculation_details': {k: v.get('calculation') for k, v in kpi_data.get('details', {}).items()}
                }
                upsert_data.append(processed_data)
        except Exception as e:
            logger.error(f"Error al obtener KPI para {nemo}: {e}", exc_info=True)

    return upsert_data

def _save_kpi_results(results: list[dict]):
    """Guarda una lista de resultados de KPI en la base de datos mediante upsert."""
    if not results:
        return
    
    stmt = insert(AdvancedKPI).values(results)
    
    update_dict = {
        col.name: col for col in stmt.excluded if col.name != 'nemo'
    }

    stmt = stmt.on_conflict_do_update(
        index_elements=['nemo'],
        set_=update_dict
    )
    db.session.execute(stmt)
    db.session.commit()
    logger.info(f"Se han insertado/actualizado {len(results)} registros de KPI.")

@api_bp.route("/bot-status", methods=["GET"])
def bot_status():
    return jsonify({"is_running": is_bot_busy()})


@api_bp.route("/stocks/update", methods=["POST"])
def update_stocks():
    data = request.get_json(silent=True) or {}
    is_auto_update = data.get('is_auto_update', False)
    
    if is_auto_update and is_bot_busy():
        logger.info("[API] Se omite auto-actualización porque ya hay un proceso en curso.")
        return jsonify({"success": False, "message": "Proceso de bot ya está activo, auto-actualización omitida."}), 200

    if not _sync_bot_running_lock.acquire(blocking=False):
        return jsonify({"success": False, "message": "Ya hay una actualización de acciones en curso."}), 409
    
    app_instance = current_app._get_current_object()  # type: ignore
    with app_instance.app_context():
        stock_filter = StockFilter.query.first()
        filtered_symbols = json.loads(stock_filter.codes_json or '[]') if stock_filter and not stock_filter.all else None
        if filtered_symbols:
             logger.info(f"[API] Se aplicará un filtro para la actualización. Símbolos: {filtered_symbols}")

    username = os.getenv("BOLSA_USERNAME")
    password = os.getenv("BOLSA_PASSWORD")

    def target_func(app, uname, pwd, symbols):
        try:
            with app.app_context():
                loop = app.bot_event_loop
                if not loop.is_running():
                    raise RuntimeError("El loop de eventos del bot no está activo al iniciar la actualización de acciones.")
                
                future = asyncio.run_coroutine_threadsafe(
                    run_bolsa_bot(app=app, username=uname, password=pwd, filtered_symbols=symbols), 
                    loop
                )
                future.result(timeout=400)
        except Exception as e:
            logger.error(f"Error CRÍTICO dentro del hilo de actualización de acciones: {e}", exc_info=True)
        finally:
            if _sync_bot_running_lock.locked():
                _sync_bot_running_lock.release()
            logger.info("[API] Lock de actualización de acciones liberado.")
    
    thread_args = (app_instance, username, password, filtered_symbols)
    threading.Thread(target=target_func, args=thread_args, daemon=True).start()
    return jsonify({"success": True, "message": "Proceso de actualización de acciones iniciado."}), 202


@api_bp.route("/dividends/update", methods=["POST"])
def update_dividends():
    app_instance = current_app._get_current_object()  # type: ignore
    def task_in_thread(app):
        result = {}
        try:
            loop = app.bot_event_loop
            if not loop.is_running(): raise RuntimeError(BOT_EVENT_LOOP_NOT_RUNNING_ERROR)
            async def update_task():
                page = await get_page()
                with app.app_context():
                    return await dividend_service.compare_and_update_dividends(page)
            future = asyncio.run_coroutine_threadsafe(update_task(), loop)
            result = future.result(timeout=120)
        except Exception as e:
            logger.error(f"Error en el hilo de actualización de dividendos: {e}", exc_info=True)
            result = {"error": str(e)}
        finally:
            socketio.emit('dividend_update_complete', result)
    threading.Thread(target=task_in_thread, args=(app_instance,), daemon=True).start()
    return jsonify({"success": True, "message": "Proceso de actualización de dividendos iniciado."}), 202


@api_bp.route("/closing/update", methods=["POST"])
def update_closing_data():
    app_instance = current_app._get_current_object()  # type: ignore
    def task_in_thread(app):
        result = {}
        try:
            loop = app.bot_event_loop
            if not loop.is_running(): raise RuntimeError(BOT_EVENT_LOOP_NOT_RUNNING_ERROR)
            async def update_task():
                page = await get_page()
                with app.app_context():
                    return await closing_service.update_stock_closings(page)
            future = asyncio.run_coroutine_threadsafe(update_task(), loop)
            result = future.result(timeout=120)
        except Exception as e:
            logger.error(f"Error en el hilo de actualización de Cierre Bursátil: {e}", exc_info=True)
            result = {"error": str(e)}
        finally:
            socketio.emit('closing_update_complete', result)
    threading.Thread(target=task_in_thread, args=(app_instance,), daemon=True).start()
    return jsonify({"success": True, "message": "Proceso de actualización de Cierre Bursátil iniciado."}), 202


@api_bp.route("/kpis/update", methods=["POST"])
def update_advanced_kpis():
    app_instance = current_app._get_current_object()  # type: ignore
    def task_in_thread(app):
        with app.app_context():
            try:
                loop = app.bot_event_loop
                if not loop.is_running(): 
                    raise RuntimeError(BOT_EVENT_LOOP_NOT_RUNNING_ERROR)
                
                page_future = asyncio.run_coroutine_threadsafe(get_page(), loop)
                page = page_future.result(timeout=60)
                
                socketio.emit('kpi_update_progress', {'status': 'info', 'message': 'Actualizando datos base de Cierre Bursátil...'})
                closing_future = asyncio.run_coroutine_threadsafe(closing_service.update_stock_closings(page), loop)
                closing_result = closing_future.result(timeout=120)

                if 'error' in closing_result:
                    raise RuntimeError(f"Fallo al obtener datos base de cierre: {closing_result['error']}")

                socketio.emit('kpi_update_progress', {'status': 'info', 'message': '✓ Datos base actualizados. Iniciando consulta de KPIs...'})

                nemos_to_update = [s.nemo for s in KpiSelection.query.all()]
                if not nemos_to_update:
                    socketio.emit('kpi_update_complete', {'message': 'No hay acciones seleccionadas para actualizar.'})
                    return
                
                future = asyncio.run_coroutine_threadsafe(
                    _fetch_and_process_kpis(nemos_to_update), loop
                )
                all_results = future.result(timeout=600)

                _save_kpi_results(all_results)
                
                socketio.emit('kpi_update_complete', {'message': f'Actualización de KPIs completada para {len(all_results)} acciones.'})

            except Exception as e:
                logger.error(f"Error en el proceso de actualización de KPIs: {e}", exc_info=True)
                socketio.emit('kpi_update_complete', {'error': str(e)})

    threading.Thread(target=task_in_thread, args=(app_instance,), daemon=True).start()
    return jsonify({"success": True, "message": "Proceso de actualización de KPIs iniciado para acciones seleccionadas."}), 202