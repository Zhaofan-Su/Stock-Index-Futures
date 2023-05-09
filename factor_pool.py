import pandas as pd
import numpy as np
from factor_weight import get_volatility_df

def check_threshold(data:pd.DataFrame, threshold:float) -> pd.DataFrame:
    data = data.div(data.abs().sum(axis=1), axis=0)
    for idx in range(1,len(data)):
        if abs(data.at[data.index[idx], '1B0300'] - data.at[data.index[idx], '1B0852']) <= threshold:
            # 延续上一日交易方向, True为做多
            direction = data.loc[data.index[idx-1],:] > 0
            direction = direction.map(lambda x: 1 if x else -1)
            # data.loc[data.index[idx],:] = data.loc[data.index[idx-1],:]
            data.loc[data.index[idx], :] = data.loc[data.index[idx],:].multiply(direction)
    return data

def ts_mome(data: pd.DataFrame, period: int) -> pd.DataFrame:
    """ 周期时序动量因子, 做多因子值为正的, 做空为负的, 按照因子值归一化加权分配仓位

    Args:
        data (pd.DataFrame): _description_
        period (int): 周期

    Returns:
        pd.DataFrame: _description_
    """
    ret_df = data.pct_change()
    volatility_df = get_volatility_df(data, period)
    volatility_df = volatility_df.apply(lambda x:np.square(x),axis=0)
    factor_value = ret_df.rolling(period).sum().div(volatility_df)
    # 因子值相差小于threshold的按照上一日操作
    # factor_value = check_threshold(factor_value, threshold)

    def get_sign(series:pd.Series)->pd.Series:
        if np.isnan(series['1B0300']) or np.isnan(series['1B0852']):
            series['1B0300'] = np.nan
            series['1B0852'] = np.nan
        # if (series['1B0300'] >= 0 and series['1B0852'] < 0) or (series['1B0300'] <= 0 and series['1B0852'] > 0):
            # 两者反向
            # series['1B0300'] = series['1B0300']/series.abs().sum()
            # series['1B0852'] = series['1B0852']/series.abs().sum()
        # else:
        if (series['1B0300'] >= 0 and series['1B0852'] >= 0) or (series['1B0300'] <= 0 and series['1B0852'] <= 0):

            # 两者同向
            if (series['1B0300']- series['1B0852']) > 0:
                series['1B0300'] = abs(series['1B0300']) 
                series['1B0852'] = -abs(series['1B0852'])
            else:
                series['1B0300'] = -abs(series['1B0300'])
                series['1B0852'] = abs(series['1B0852'])

        return series
    
    factor_sign = factor_value.apply(lambda x:get_sign(x), axis=1)
    
    return factor_value

def pn_mome(data, period:int) -> pd.DataFrame:
    """ 周期截面动量因子, 均仓做多因子值大的品种，做空因子值小的品种

    Args:
        n (int): 周期长短

    Returns:
        pd.DataFrame: 因子值dataframe, 每行为一天, 每列为一个品种
    """
    ret_data = data.apply(lambda x: np.log(x).diff(1), axis=0)
    # 因子值
    factor_value = ret_data.apply(lambda x:x.rolling(period).sum())
    # 因子值相差小于threshold的按照上一日操作
    # factor_value = check_threshold(factor_value, threshold)
    # 均仓做多因子值大的品种，做空因子值小的品种
    def get_sign(series:pd.Series) -> pd.Series:
        if np.isnan(series['1B0300']) or np.isnan(series['1B0852']):
            series['1B0300'] = np.nan
            series['1B0852'] = np.nan
        if series['1B0300'] >= series['1B0852']:
            series['1B0300'] = 0.5
            series['1B0852'] = -0.5
        else:
            series['1B0300'] = -0.5
            series['1B0852'] = 0.5
        return series

    # 因子信号
    factor_sign = factor_value.apply(lambda x:get_sign(x), axis=1)

    return factor_value