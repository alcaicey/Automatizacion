# src/routes/api/data_routes.py
import logging
from flask import jsonify, request, current_app, Blueprint
from sqlalchemy import select, and_, func, or_
from datetime import datetime, time
import pandas as pd
from flask_login import login_required

from src.utils.db_io import get_latest_data, filter_stocks, compare_last_two_db_entries
from src.utils import history_view
from src.extensions import db
from src.models import (
    StockPrice, Dividend, StockClosing, AdvancedKPI, KpiSelection, FilteredStockHistory,
    AnomalousEvent, Portfolio, Alert, DividendColumnPreference
)

logger = logging.getLogger(__name__)

data_bp = Blueprint('data', __name__)

@data_bp.route('/all_stock_symbols', methods=['GET'])
def get_all_stock_symbols():
    """Devuelve una lista de todos los símbolos de acciones únicos."""
    try:
        # Usamos distinct() para obtener solo valores únicos y evitar duplicados
        # y filtramos para no incluir símbolos nulos o vacíos.
        symbols_query = db.session.query(StockPrice.symbol).filter(StockPrice.symbol.isnot(None)).distinct()
        symbols = [s[0] for s in symbols_query.all()]
        return jsonify(symbols)
    except Exception as e:
        logger.error(f"Error al obtener todos los símbolos de acciones: {e}")
        return jsonify({'error': 'Error interno al obtener la lista de símbolos'}), 500

@data_bp.route("/stocks", methods=["GET"])
def get_stocks():
    with current_app.app_context():
        stock_codes = request.args.getlist("code")
        result = filter_stocks(stock_codes) if stock_codes else get_latest_data()
        
        # Aseguramos que la respuesta siempre tenga la estructura {stocks: [], last_update: ""}
        if 'stocks' not in result:
            # Si el resultado es una lista simple, la envolvemos
            return jsonify({'stocks': result, 'last_update': None})
        
        return jsonify(result)

@data_bp.route("/history", methods=["GET"])
def history_list():
    with current_app.app_context():
        return jsonify(history_view.load_history())

@data_bp.route("/history/compare", methods=["GET"])
def history_compare():
    with current_app.app_context():
        stock_codes = request.args.getlist("code")
        comparison_data = compare_last_two_db_entries(stock_codes=stock_codes if stock_codes else None)
        return jsonify(comparison_data or history_view.compare_latest(stock_codes=stock_codes if stock_codes else None) or {})

@data_bp.route("/stocks/history/<symbol>", methods=["GET"])
def stock_history(symbol):
    with current_app.app_context():
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        granularity = request.args.get("granularity", "hour")

        if not start_date_str or not end_date_str:
            return jsonify({"error": "Debe especificar fechas de inicio y fin."}), 400

        try:
            start_date = datetime.combine(datetime.strptime(start_date_str, '%Y-%m-%d').date(), time.min)
            end_date = datetime.combine(datetime.strptime(end_date_str, '%Y-%m-%d').date(), time.max)
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}), 400

        if granularity not in ['hour', 'day', 'week']:
            granularity = 'hour'

        time_series = func.date_trunc(granularity, StockPrice.timestamp).label("time_series")
        
        query = db.session.query(
            time_series,
            func.avg(StockPrice.price).label("price")
        ).filter(
            StockPrice.symbol == symbol.upper(),
            StockPrice.timestamp.between(start_date, end_date)
        ).group_by(time_series).order_by(time_series)
        
        prices = query.all()
        
        data = [{"x": p.time_series.isoformat(), "y": float(p.price)} for p in prices]
        
        return jsonify({"data": data})

@data_bp.route("/dividends", methods=["GET"])
def get_dividends():
    with current_app.app_context():
        logger.info("[API /dividends] Petición recibida.")
        latest_closing_date = db.session.query(func.max(StockClosing.date)).scalar()
        logger.info(f"[API /dividends] Última fecha de cierre encontrada: {latest_closing_date}")
        
        if not latest_closing_date:
            logger.warning("[API /dividends] No se encontraron datos de cierre bursátil. Devolviendo lista de dividendos vacía.")
            return jsonify([])

        logger.info("[API /dividends] Construyendo consulta base de dividendos...")
        query = db.session.query(
            Dividend,
            # Se usa una subconsulta para la columna 'belongs_to_ipsa' para evitar que el outerjoin filtre todo
            select(StockClosing.belongs_to_ipsa)
            .where(StockClosing.nemo == Dividend.nemo)
            .where(StockClosing.date == latest_closing_date)
            .label('is_ipsa')
        )
        logger.info("[API /dividends] Consulta base construida.")

        if start_date_str := request.args.get('start_date'):
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            query = query.filter(Dividend.payment_date >= start_date)
            logger.info(f"[API /dividends] Filtro por fecha de inicio aplicado: {start_date}")

        if end_date_str := request.args.get('end_date'):
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            query = query.filter(Dividend.payment_date <= end_date)
            logger.info(f"[API /dividends] Filtro por fecha de fin aplicado: {end_date}")
            
        # El filtro de IPSA ahora se aplica sobre la subconsulta, que puede ser nula
        if request.args.get('is_ipsa') == 'true':
            query = query.filter(
                select(StockClosing.belongs_to_ipsa)
                .where(StockClosing.nemo == Dividend.nemo)
                .where(StockClosing.date == latest_closing_date)
                .as_scalar() == True
            )
            logger.info("[API /dividends] Filtro IPSA aplicado.")

        if search_text := request.args.get('search_text', '').strip():
            column_map = {
                'nemo': Dividend.nemo,
                'descrip_vc': Dividend.description,
            }
            search_column_key = request.args.get('search_column')
            
            if search_column_key in column_map:
                search_column = column_map[search_column_key]
                query = query.filter(search_column.ilike(f"%{search_text}%"))
            else:
                query = query.filter(
                    or_(
                        Dividend.nemo.ilike(f"%{search_text}%"),
                        Dividend.description.ilike(f"%{search_text}%")
                    )
                )
            logger.info(f"[API /dividends] Filtro de búsqueda de texto aplicado: '{search_text}'")

        logger.info("[API /dividends] Ejecutando consulta final a la base de datos...")
        results = query.order_by(Dividend.payment_date.asc()).all()
        logger.info(f"[API /dividends] Consulta completada. {len(results)} registros encontrados.")
        
        enriched_dividends = []
        for dividend, belongs_to_ipsa in results:
            dividend_dict = dividend.to_dict()
            dividend_dict['is_ipsa'] = bool(belongs_to_ipsa)
            enriched_dividends.append(dividend_dict)
            
        logger.info(f"[API /dividends] Devolviendo {len(enriched_dividends)} dividendos enriquecidos.")
        return jsonify(enriched_dividends)

@data_bp.route("/closing", methods=["GET"])
def get_closing_data():
    with current_app.app_context():
        nemos_to_filter = request.args.getlist("nemo")
        latest_date = db.session.query(func.max(StockClosing.date)).scalar()
        if not latest_date: return jsonify([])
        query = StockClosing.query.filter_by(date=latest_date)
        if nemos_to_filter:
            logger.info(f"[API /closing] Filtrando Cierre Bursátil por: {nemos_to_filter}")
            query = query.filter(StockClosing.nemo.in_(nemos_to_filter))
        closings = query.order_by(StockClosing.nemo).all()
        return jsonify([c.to_dict() for c in closings])

@data_bp.route("/kpis", methods=["GET"])
def get_all_kpis():
    with current_app.app_context():
        logger.info("[API /kpis] Petición recibida.")
        
        selected_nemos_query = select(KpiSelection.nemo)
        selected_nemos = [row.nemo for row in db.session.execute(selected_nemos_query).all()]
        logger.info(f"[API /kpis] {len(selected_nemos)} nemotécnicos seleccionados para KPIs.")
        
        if not selected_nemos:
            logger.info("[API /kpis] No hay nemotécnicos seleccionados, devolviendo array vacío.")
            return jsonify([])

        latest_date = db.session.query(func.max(StockClosing.date)).scalar()
        logger.info(f"[API /kpis] Última fecha de cierre encontrada: {latest_date}")
        if not latest_date:
            logger.info("[API /kpis] No hay fecha de cierre, devolviendo array vacío.")
            return jsonify([])

        logger.info("[API /kpis] Realizando consulta de datos de cierre...")
        closings = StockClosing.query.filter(StockClosing.nemo.in_(selected_nemos), StockClosing.date == latest_date).all()
        logger.info(f"[API /kpis] Consulta de cierre completada. {len(closings)} registros encontrados.")

        logger.info("[API /kpis] Realizando consulta de KPIs avanzados...")
        advanced_kpis_query = AdvancedKPI.query.filter(AdvancedKPI.nemo.in_(selected_nemos)).all()
        advanced_kpis = {k.nemo: k.to_dict() for k in advanced_kpis_query}
        logger.info(f"[API /kpis] Consulta de KPIs avanzados completada. {len(advanced_kpis)} registros encontrados.")
        
        combined_data = []
        for closing in closings:
            data = closing.to_dict()
            adv_data = advanced_kpis.get(data['nemo'], {})
            data['roe'] = adv_data.get('roe')
            data['debt_to_equity'] = adv_data.get('debt_to_equity')
            data['beta'] = adv_data.get('beta')
            data['riesgo'] = adv_data.get('analyst_recommendation') or 'Pendiente'
            data['dividend_yield'] = data.get('ren_actual')
            data['kpi_last_updated'] = adv_data.get('last_updated')
            data['kpi_source'] = adv_data.get('source')
            combined_data.append(data)
            
        logger.info(f"[API /kpis] Devolviendo {len(combined_data)} registros combinados.")
        return jsonify(combined_data)

@data_bp.route("/dashboard/chart-data", methods=["GET"])
def get_dashboard_chart_data():
    with current_app.app_context():
        stock_symbols = request.args.getlist("stock")
        metric = request.args.get("metric", "price")
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        granularity = request.args.get("granularity", "hour")

        if not stock_symbols: return jsonify({"error": "Debe especificar al menos un símbolo."}), 400
        if not start_date_str or not end_date_str: return jsonify({"error": "Debe especificar fechas de inicio y fin."}), 400

        try:
            start_date = datetime.combine(datetime.strptime(start_date_str, '%Y-%m-%d').date(), time.min)
            end_date = datetime.combine(datetime.strptime(end_date_str, '%Y-%m-%d').date(), time.max)
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}), 400
        
        valid_metrics = {
            "price": func.avg(FilteredStockHistory.price),
            "price_difference": func.sum(FilteredStockHistory.price_difference),
            "percent_change": func.sum(FilteredStockHistory.percent_change)
        }
        if metric not in valid_metrics: return jsonify({"error": "Métrica no válida."}), 400

        # Truncar la fecha/hora según la granularidad
        if granularity not in ['hour', 'day', 'week']:
            granularity = 'hour' # Valor por defecto seguro
        
        time_series = func.date_trunc(granularity, FilteredStockHistory.timestamp).label("time_series")
        
        query = db.session.query(
            FilteredStockHistory.symbol,
            time_series,
            valid_metrics[metric].label("value")
        ).filter(
            FilteredStockHistory.symbol.in_(stock_symbols),
            FilteredStockHistory.timestamp.between(start_date, end_date)
        ).group_by(
            FilteredStockHistory.symbol,
            time_series
        ).order_by(
            time_series
        )
        
        history_data = query.all()

        chart_data = {symbol: [] for symbol in stock_symbols}
        for symbol, timestamp, value in history_data:
            if value is not None:
                chart_data[symbol].append({"x": timestamp.isoformat(), "y": float(value)})
        
        return jsonify(chart_data)

@data_bp.route("/news", methods=["GET"])
def get_financial_news():
    """
    Devuelve noticias financieras.
    NOTA: Actualmente utiliza datos de ejemplo (mock). En el futuro,
    se conectará a una API de noticias real.
    """
    portfolio_symbols = request.args.getlist("symbol") # Para filtrar noticias por portafolio
    
    mock_news = [
        {"id": 1, "source": "Diario Financiero", "headline": "CENCOSUD anuncia plan de expansión en Brasil y sus acciones suben un 2.5%", "timestamp": "2023-10-27T10:30:00Z", "sentiment": "positive", "symbols": ["CENCOSUD"]},
        {"id": 2, "source": "Reuters", "headline": "Sector aéreo enfrenta turbulencias por alza del petróleo; LTM cae ligeramente", "timestamp": "2023-10-27T09:15:00Z", "sentiment": "negative", "symbols": ["LTM"]},
        {"id": 3, "source": "Bloomberg", "headline": "Análisis: ¿Es RIPLEY una buena inversión a largo plazo? Opiniones divididas.", "timestamp": "2023-10-27T08:00:00Z", "sentiment": "neutral", "symbols": ["RIPLEY"]},
        {"id": 4, "source": "La Tercera", "headline": "Gobierno anuncia nuevo paquete de estímulos para el sector construcción.", "timestamp": "2023-10-26T20:00:00Z", "sentiment": "positive", "symbols": []}
    ]

    # Filtrar noticias si se proporcionan símbolos
    if portfolio_symbols:
        filtered_news = [news for news in mock_news if any(s in news.get("symbols", []) for s in portfolio_symbols)]
        return jsonify(filtered_news)

    return jsonify(mock_news)

@data_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Obtiene todas las alertas activas."""
    try:
        alerts = Alert.query.filter_by(status='active').all()
        return jsonify([alert.to_dict() for alert in alerts])
    except Exception as e:
        logger.error(f"Error al obtener alertas: {e}")
        return jsonify({'error': 'Error interno al obtener alertas'}), 500

@data_bp.route('/alerts', methods=['POST'])
def create_alert():
    """Crea una nueva alerta de precio."""
    data = request.get_json()
    if not data or 'symbol' not in data or 'target_price' not in data or 'condition' not in data:
        return jsonify({'error': 'Datos incompletos para crear la alerta'}), 400

    try:
        new_alert = Alert(
            symbol=data['symbol'],
            target_price=float(data['target_price']),
            condition=data['condition'] # 'above' or 'below'
        )
        db.session.add(new_alert)
        db.session.commit()
        return jsonify(new_alert.to_dict()), 201
    except ValueError:
        return jsonify({'error': 'El precio objetivo debe ser un número válido'}), 400
    except Exception as e:
        logger.error(f"Error al crear alerta: {e}")
        db.session.rollback()
        return jsonify({'error': 'Error interno al crear la alerta'}), 500

@data_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
def cancel_alert(alert_id):
    """Cancela una alerta (la marca como 'cancelled')."""
    try:
        alert = db.session.get(Alert, alert_id)
        if not alert:
            return jsonify({'error': 'Alerta no encontrada'}), 404
        
        alert.status = 'cancelled'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Alerta cancelada'})
    except Exception as e:
        logger.error(f"Error al cancelar alerta {alert_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Error interno al cancelar la alerta'}), 500

@data_bp.route('/stock_history/<symbol>', methods=['GET'])
def get_stock_history(symbol):
    """Devuelve el historial de precios para un símbolo específico con granularidad y SMA opcional."""
    start_date_str = request.args.get('start')
    end_date_str = request.args.get('end')
    granularity = request.args.get('granularity', 'day') # 'hour', 'day', 'week'
    sma_period_str = request.args.get('sma_period')

    try:
        query = StockPrice.query.filter_by(symbol=symbol)

        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(StockPrice.timestamp >= start_date)
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            query = query.filter(StockPrice.timestamp <= end_date)

        if granularity == 'hour':
            trunc_field = func.DATE_TRUNC('hour', StockPrice.timestamp)
        elif granularity == 'week':
            trunc_field = func.DATE_TRUNC('week', StockPrice.timestamp)
        else: # 'day' es el por defecto
            trunc_field = func.DATE_TRUNC('day', StockPrice.timestamp)
            
        aggregated_query = db.session.query(
            trunc_field.label('time_bucket'),
            func.avg(StockPrice.price).label('price')
        ).filter(StockPrice.symbol == symbol)
        
        if start_date_str:
            aggregated_query = aggregated_query.filter(StockPrice.timestamp >= start_date)
        if end_date_str:
            aggregated_query = aggregated_query.filter(StockPrice.timestamp <= end_date)

        aggregated_query = aggregated_query.group_by('time_bucket').order_by('time_bucket')
        
        history = aggregated_query.all()
        
        # Convertir a DataFrame de pandas para calcular SMA
        df = pd.DataFrame([{'timestamp': r.time_bucket, 'price': r.price} for r in history])

        if not df.empty and sma_period_str and sma_period_str.isdigit():
            sma_period = int(sma_period_str)
            if sma_period > 1 and sma_period < len(df):
                df[f'sma_{sma_period}'] = df['price'].rolling(window=sma_period).mean()

        # Reemplazar NaN por None para que sea compatible con JSON
        df = df.where(pd.notnull(df), None)

        response_data = df.to_dict(orient='records')
        
        # Convertir timestamps a string
        for record in response_data:
            record['timestamp'] = record['timestamp'].isoformat() if record.get('timestamp') else None

        return jsonify(response_data)

    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido. Usar YYYY-MM-DD.'}), 400

@data_bp.route('/kpi/analyze/<nemo>', methods=['GET'])
async def analyze_kpi(nemo):
    """
    Endpoint para solicitar el análisis de IA para un único KPI a pedido.
    """
    logger.info(f"Iniciando análisis de KPI para: {nemo}")
    try:
        from src.services.ai_financial_service import AIFinancialService
        
        logger.debug(f"[{nemo}] Inicializando AIFinancialService...")
        # NOTE: Se pasa `None` como API key. El servicio debe poder manejarlo.
        service = AIFinancialService(None)
        
        logger.debug(f"[{nemo}] Ejecutando 'calculate_and_store_single_kpi'...")
        kpi_data = await service.calculate_and_store_single_kpi(nemo)
        logger.debug(f"[{nemo}] Finalizó 'calculate_and_store_single_kpi'.")
        
        if not kpi_data:
            logger.warning(f"[{nemo}] No se pudo calcular el KPI. El servicio no devolvió datos.")
            return jsonify({"error": "No se pudo calcular el KPI para el nemo proporcionado."}), 404
            
        logger.info(f"[{nemo}] Análisis completado con éxito. Devolviendo datos.")
        return jsonify({"data": kpi_data})
        
    except Exception as e:
        logger.error(f"ERROR en /api/kpi/analyze/{nemo}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@data_bp.route('/dividends/columns', methods=['GET', 'POST'])
@login_required
def dividend_columns():
    if request.method == 'POST':
        data = request.get_json()
        new_prefs = data.get('columns', [])
        DividendColumnPreference.query.filter_by(user_id=current_user.id).delete()
        for col_name in new_prefs:
            pref = DividendColumnPreference(user_id=current_user.id, column_name=col_name)
            db.session.add(pref)
        db.session.commit()
        return jsonify({"message": "Preferencias guardadas"})

    all_columns = ['nemo', 'is_ipsa', 'descrip_vc', 'fec_lim', 'fec_pago', 'moneda', 'val_acc', 'num_acc_ant', 'num_acc_der', 'num_acc_nue', 'pre_ant_vc', 'pre_ex_vc']
    user_prefs = DividendColumnPreference.query.filter_by(user_id=current_user.id).all()
    visible_columns = [p.column_name for p in user_prefs]
    if not visible_columns:
        visible_columns = ['nemo', 'descrip_vc', 'fec_lim', 'fec_pago', 'val_acc', 'pre_ex_vc']
        
    return jsonify({
        "all_columns": all_columns,
        "visible_columns": visible_columns
    })