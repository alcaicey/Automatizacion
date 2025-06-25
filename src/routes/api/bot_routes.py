# src/routes/api/bot_routes.py

import asyncio
import json
import logging
import os
import threading
import time
from flask import jsonify, current_app
from sqlalchemy.dialects.postgresql import insert

from src.routes.api import api_bp
from src.models import StockFilter, AdvancedKPI, KpiSelection

from src.scripts.bolsa_service import run_bolsa_bot
from src.scripts import dividend_service, closing_service, ai_financial_service
from src.scripts.bot_page_manager import get_page
from src.extensions import socketio, db

logger = logging.getLogger(__name__)
_sync_bot_running_lock = threading.Lock()


@api_bp.route("/bot-status", methods=["GET"])
def bot_status():
    is_running = _sync_bot_running_lock.locked()
    return jsonify({"is_running": is_running})


@api_bp.route("/stocks/update", methods=["POST"])
def update_stocks():
    if not _sync_bot_running_lock.acquire(blocking=False):
        return jsonify({"success": False, "message": "Ya hay una actualización de acciones en curso."}), 409
    
    app_instance = current_app._get_current_object()
    with app_instance.app_context():
        stock_filter = StockFilter.query.first()
        filtered_symbols = None
        if stock_filter and not stock_filter.all:
            filtered_symbols = json.loads(stock_filter.codes_json or '[]')
            logger.info(f"[API] Se aplicará un filtro para la actualización de precios. Símbolos: {filtered_symbols}")

    username = os.getenv("BOLSA_USERNAME")
    password = os.getenv("BOLSA_PASSWORD")
    
    bot_kwargs = {
        "app": app_instance, 
        "username": username, 
        "password": password,
        "filtered_symbols": filtered_symbols
    }

    def target_func(app):
        try:
            with app.app_context():
                loop = app.bot_event_loop
                future = asyncio.run_coroutine_threadsafe(run_bolsa_bot(**bot_kwargs), loop)
                future.result(timeout=300)
        finally:
            if _sync_bot_running_lock.locked():
                _sync_bot_running_lock.release()
            logger.info("[API] Lock de actualización de acciones liberado.")
    
    threading.Thread(target=target_func, args=(app_instance,), daemon=True).start()
    return jsonify({"success": True, "message": "Proceso de actualización de acciones iniciado."}), 202


@api_bp.route("/dividends/update", methods=["POST"])
def update_dividends():
    app_instance = current_app._get_current_object()
    def task_in_thread(app):
        result = {}
        try:
            loop = app.bot_event_loop
            if not loop.is_running(): raise RuntimeError("El loop de eventos del bot no está corriendo.")
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
    app_instance = current_app._get_current_object()
    def task_in_thread(app):
        result = {}
        try:
            loop = app.bot_event_loop
            if not loop.is_running(): raise RuntimeError("El loop de eventos del bot no está corriendo.")
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
    app_instance = current_app._get_current_object()
    def task_in_thread(app):
        with app.app_context():
            nemo = "" # variable para logging en caso de error
            try:
                loop = app.bot_event_loop
                if not loop.is_running(): raise RuntimeError("El loop de eventos del bot no está corriendo.")
                
                page_future = asyncio.run_coroutine_threadsafe(get_page(), loop)
                page = page_future.result(timeout=60)
                
                socketio.emit('kpi_update_progress', {'status': 'info', 'message': 'Actualizando datos base de Cierre Bursátil...'})
                closing_future = asyncio.run_coroutine_threadsafe(closing_service.update_stock_closings(page), loop)
                closing_result = closing_future.result(timeout=120)

                if 'error' in closing_result:
                    raise Exception(f"Fallo al obtener datos base de cierre: {closing_result['error']}")

                socketio.emit('kpi_update_progress', {'status': 'info', 'message': '✓ Datos base actualizados. Iniciando consulta de KPIs...'})

                nemos_to_update = [s.nemo for s in KpiSelection.query.all()]
                if not nemos_to_update:
                    socketio.emit('kpi_update_complete', {'message': 'No hay acciones seleccionadas para actualizar.'})
                    return
                
                updated_count = 0
                for i, nemo in enumerate(nemos_to_update):
                    kpi_data = ai_financial_service.get_advanced_kpis(nemo)
                    if kpi_data:
                        data_to_upsert = {
                            "nemo": nemo, "roe": kpi_data.get('roe'),
                            "debt_to_equity": kpi_data.get('debt_to_equity'),
                            "beta": kpi_data.get('beta'),
                            "analyst_recommendation": kpi_data.get('analyst_recommendation'),
                            "source": kpi_data.get('source')
                        }
                        stmt = insert(AdvancedKPI).values(data_to_upsert)
                        update_stmt = stmt.on_conflict_do_update(index_elements=['nemo'], set_=data_to_upsert)
                        db.session.execute(update_stmt)
                        db.session.commit()
                        updated_count += 1
                        socketio.emit('kpi_update_progress', {'nemo': nemo, 'status': 'success', 'progress': f"{i+1}/{len(nemos_to_update)}"})
                    else:
                        socketio.emit('kpi_update_progress', {'nemo': nemo, 'status': 'failed', 'progress': f"{i+1}/{len(nemos_to_update)}"})
                    time.sleep(1.5) 
                
                socketio.emit('kpi_update_complete', {'message': f'Actualización completada. {updated_count} de {len(nemos_to_update)} acciones procesadas.'})

            except Exception as e:
                logger.error(f"Error procesando KPI para {nemo}: {e}", exc_info=True)
                socketio.emit('kpi_update_complete', {'error': str(e)})

    threading.Thread(target=task_in_thread, args=(app_instance,), daemon=True).start()
    return jsonify({"success": True, "message": "Proceso de actualización de KPIs iniciado para acciones seleccionadas."}), 202