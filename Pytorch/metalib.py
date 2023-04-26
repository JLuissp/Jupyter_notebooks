
import MetaTrader5 as mt5
from datetime import datetime
import numpy as np
import pandas as pd
import pytz
from scipy.signal import argrelextrema


def range_ticks(symbol,start_date,final_date,time_frame = 'H1'):
    
    '''
    Returns a dataframe with the range from start_date to final_date:
    
        args:
        symbo -> 'str'  pair/instrument acronym.
        start_date -> 'tuple' (Y, M, D): start date from where the data will be extracted.
        final_date -> 'tuple' Y, M, D): final date of the range
        time_frame: 'str' = 'H1'

        Example:

        range_ticks(USDJPY,(),final_date,time_frame = 'H1')

    '''
    
    timeframe = {
        'M1': mt5.TIMEFRAME_M1,
        'M5':mt5.TIMEFRAME_M5,
        'M30':mt5.TIMEFRAME_M30,
        'H1':mt5.TIMEFRAME_H1,
        'H4':mt5.TIMEFRAME_H4,
        'D1':mt5.TIMEFRAME_D1
        } 
    
    if not mt5.initialize():
        print("initialize() failed, error code =",mt5.last_error())
        quit()
    
    # establecemos el huso horario en UTC
    timezone = pytz.timezone("Etc/UTC")
    
    Y,M,D = start_date
    Y2,M2,D2 = final_date
    
    # creamos los objetos datetime en el huso horario UTC, para que no se aplique el desplazamiento del huso horario local
    date_from = datetime(Y, M, D, tzinfo=timezone)
    date_to= datetime(Y2, M2, D2, tzinfo=timezone)
    
    rates = mt5.copy_rates_range(symbol, timeframe[time_frame], date_from, date_to)
    mt5.shutdown()
    
    #creamos el dataframe:
    rates_frame = pd.DataFrame(rates)
    # convertimos la hora en segundos al formato datetime
    rates_frame['time']=pd.to_datetime(rates_frame['time'], unit='s')
    
    return rates_frame


def get_nbars(symbol, time_frame = 'H1', i_bar = 0, n_bars = 100):
    '''
    Return n_bars counting backwards in time starting from i_bar (0 means the present bar).
    
            args:
            symbol: 'str'  pair/instrument acronym.
            time_frame: 'str' = 'H1'
            n_bars: 'int' = 100
            i_bar: 'int' = 0
    '''
    timeframe = {
        'M1': mt5.TIMEFRAME_M1,
        'M5':mt5.TIMEFRAME_M5,
        'M30':mt5.TIMEFRAME_M30,
        'H1':mt5.TIMEFRAME_H1,
        'H4':mt5.TIMEFRAME_H4,
        'D1':mt5.TIMEFRAME_D1
        } 
    
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return None
    
    bars = mt5.copy_rates_from_pos(symbol, timeframe[time_frame], i_bar, n_bars)
    # finalizamos la conexión con el terminal MetaTrader 5
    mt5.shutdown()
    
    bars_df = pd.DataFrame(bars)
    bars_df['time']=pd.to_datetime(bars_df['time'], unit='s')
    return bars_df
    
    
    
    
def get_higher_values(data, window = 5, column='high'):

    highs = data.iloc[argrelextrema(data[column].values,
                                   np.greater_equal, order=window)]
    return highs

def get_lower_values(data, window=5, column = 'low'):
    lows = data.iloc[argrelextrema(data[column].values,
                                  np.less_equal,order=window)]
    return lows
    

    
def get_cross(dataf: pd.DataFrame,feature_1 = 'close',feature_2 = 'EMA',cross='over'):

    import numpy as np
    import warnings
    warnings.filterwarnings('ignore')
    dataframe = dataf.copy(deep=True)
    '''
    cross = {
    'over': 1
    'under': -1
    }
    
    to visualize the points use: 
    ax.scatter(df[df['position'] == 1 ].index,df[feature_1][df['position'] == 1 ].values,s=25, marker = '^',c='#007502')
    '''
    dataframe['signal'] = 0.0
    dataframe['signal'] = np.where(dataframe[feature_1]>dataframe[feature_2],1.0,0)
    dataframe['position'] = dataframe['signal'].diff()
    if cross == 'over' or cross == 1:
        crossover_values = dataframe[dataframe['position'] == 1]
        return crossover_values
    if cross == 'under' or cross == -1:
        crossunder_values = dataframe[dataframe['position'] == -1]
        return crossunder_values

def send_buy_order(symb,lot,sl_points):
    # establecemos la conexión con el terminal MetaTrader 5
    if not mt5.initialize():
        print("initialize() failed, error code =",mt5.last_error())
        quit()
    # preparamos la estructura de la solicitud de compra
    symbol_info = mt5.symbol_info(symb)
    if symbol_info is None:
        print(symb, "not found, can not call order_check()")
        mt5.shutdown()
    # si el símbolo no está disponible en MarketWatch, lo añadimos
    if not symbol_info.visible:
        print(symb, "is not visible, trying to switch on")
        if not mt5.symbol_select(symb,True):
            print("symbol_select({}}) failed, exit",symb)
            mt5.shutdown()
            
    #point = mt5.symbol_info(symb).point
    price = mt5.symbol_info_tick(symb).ask
    deviation = 5
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symb,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY,
        "price":price,
        "sl": price - sl_points,
        "deviation": deviation,
        "magic": 234000,
        "comment": "python: sell order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    # enviamos la solicitud comercial
    result = mt5.order_send(request)
    
    
    # comprobamos el resultado de la ejecución
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("buy_order_send failed, retcode={}".format(result.retcode))
       # solicitamos el resultado en forma de diccionario y lo mostramos elemento por elemento
        mt5.shutdown()
        quit()
    print("buy_order_succed: by {} {} lots at {} with deviation={} points".format(symb,lot,price,deviation));
    mt5.shutdown()
    
    return result._asdict()

    
def send_sell_order(symb,lot, sl_points):
    # establecemos la conexión con el terminal MetaTrader 5
    if not mt5.initialize():
        print("initialize() failed, error code =",mt5.last_error())
        quit()
    # preparamos la estructura de la solicitud de compra
    symbol_info = mt5.symbol_info(symb)
    if symbol_info is None:
        print(symb, "not found, can not call order_check()")
        mt5.shutdown()
    # si el símbolo no está disponible en MarketWatch, lo añadimos
    if not symbol_info.visible:
        print(symb, "is not visible, trying to switch on")
        if not mt5.symbol_select(symb,True):
            print("symbol_select({}}) failed, exit",symb)
            mt5.shutdown()
            
    #point = mt5.symbol_info(symb).point
    price = mt5.symbol_info_tick(symb).bid
    deviation = 5
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symb,
        "volume": lot,
        "type": mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": price + sl_points,
        "deviation": deviation,
        "magic": 234000,
        "comment": "python: sell order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    # enviamos la solicitud comercial
    result = mt5.order_send(request)
    
    
    # comprobamos el resultado de la ejecución
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("sell_order_send failed, retcode={}".format(result.retcode))
       # solicitamos el resultado en forma de diccionario y lo mostramos elemento por elemento
        mt5.shutdown()
        return None
    print("sell_order_succed: by {} {} lots at {} with deviation={} points".format(symb,lot,price,deviation));
    mt5.shutdown()
    
    return result._asdict()
    
def symbol_tick(symbol):
    # establecemos la conexión con el terminal MetaTrader 5
    if not mt5.initialize():
        print("initialize() failed, error code =",mt5.last_error())
        quit()
     
    # intentamos activar la muestra del símbolo GBPUSD en MarketWatch
    selected=mt5.symbol_select(symbol,True)
    if not selected:
        print("Failed to select",symbol)
        mt5.shutdown()
        quit()
    # mostramos el último tick del símbolo GBPUSD
    lasttick=mt5.symbol_info_tick(symbol)._asdict()
    
    return lasttick
    

def close_order(ticket,pos_type, symbol, lot):
    # establecemos la conexión con el terminal MetaTrader 5
    if not mt5.initialize():
        print("initialize() failed, error code =",mt5.last_error())
        quit()
     
    # preparamos la estructura de la solicitud de compra
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(symbol, "not found, can not call order_check()")
        mt5.shutdown()
        quit()
     
    # si el símbolo no está disponible en MarketWatch, lo añadimos
    if not symbol_info.visible:
        print(symbol, "is not visible, trying to switch on")
        if not mt5.symbol_select(symbol,True):
            print("symbol_select({}}) failed, exit",symbol)
            mt5.shutdown()
    # creamos una solicitud de cierre
    if pos_type == 0 or pos_type == 'buy':
        price = mt5.symbol_info_tick(symbol).bid
        tipo = 1
    if pos_type == 1 or pos_type == 'sell':
        price = mt5.symbol_info_tick(symbol).ask
        tipo = 0
        
    deviation=5
    request={
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": tipo,
        "position": ticket,
        "price": price,
        "deviation": deviation,
        "magic": 234000,
        "comment": "python script close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result=mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("close_order_send failed, retcode={}".format(result.retcode))
    else:
        print("close_position_succeed: by {} {} at {} with ticket: {}".format(symbol,lot,price,ticket))

    return result._asdict()


def calc_profit(pos_type,symbol,lot,op,cl):
    # establecemos la conexión con el terminal MetaTrader 5
    if not mt5.initialize():
        print("initialize() failed, error code =",mt5.last_error())
        return None
    # obtenemos la divisa de la cuenta
    if pos_type == 0 or pos_type == 'buy':
        buy_profit=mt5.order_calc_profit(mt5.ORDER_TYPE_BUY,symbol,lot,op,cl)
        return buy_profit
    if pos_type == 1 or pos_type == 'sell':
        sell_profit=mt5.order_calc_profit(mt5.ORDER_TYPE_SELL,symbol,lot,op,cl)
        return sell_profit
    

def get_positions(symbol):
    # establish connection to the MetaTrader 5 terminal
    if not mt5.initialize():
        print("initialize() failed, error code =",mt5.last_error())
        return None
    # get the list of positions on symbols whose names contain "*USD*"
    positions=mt5.positions_get(symbol=symbol)
    mt5.shutdown()
    if positions==None:
        return None
    elif len(positions)>0:
        # display these positions as a table using pandas.DataFrame
        df=pd.DataFrame(list(positions),columns=positions[0]._asdict().keys())
        df.drop(['reason','time','comment','magic','identifier','time_update', 'time_msc', 'time_update_msc', 'external_id'], axis=1, inplace=True)
        return df