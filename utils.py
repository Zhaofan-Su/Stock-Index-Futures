from datetime import timedelta, datetime
from chinese_calendar import is_workday
import pandas as pd

def str2datetime(date_str: str, formatter="%Y-%m-%d") -> datetime:
    """ 将字符串时间转为datetime

    Args:
        date_str (str): 字符串时间

    Returns:
        datetime: 时间戳
    """
    dtime = datetime.strptime(date_str, formatter)
    return dtime


def find_recent_trade_day(date: datetime) -> datetime:
    """ 寻找离某个时间点最近的交易日
        如果该时间点为交易日，则返回该时间点
        否则，往前寻找

    Args:
        date (time): 时间点

    Returns:
        time: 离该时间点最近的交易日
    """

    while True:
        if is_trade_day(date):
            break
        else:
            date = date - timedelta(days=1)

    return date


def is_trade_day(date: datetime) -> bool:
    """ 判断某个日期是否为交易日

    Args:
        date (datetime): 具体日期

    """
    if is_workday(date):
        if date.isoweekday() < 6:
            return True
    return False



def build_trade_days(sdate:str, edate:str, formatter="%Y-%m-%d") -> list:
    """ 获取从sdate到edate之间的交易日  Args:
        sdate (str): 开始时间
        edate (str): 截止时间

    Returns:
        list: 日期列表
    """
    date_list = []
    s_date = str2datetime(sdate, formatter)
    e_date = str2datetime(edate, formatter)
    now_date = s_date
    flag = False
    while flag == False:
        if now_date == e_date:
            flag = True
        if is_trade_day(now_date):
            # date_list.append(datetime.strptime(now_date.strftime(formatter), formatter))
            date_list.append(now_date)
        now_date = now_date + timedelta(days=1)
    
    return date_list
        

def get_data(futures:list, indicator:str, s_date:str, e_date:str) -> pd.DataFrame:
    
    trade_days = build_trade_days(s_date, e_date)

    data_df = pd.DataFrame(index=trade_days, columns=futures)
    
    for future in futures:
        df = pd.read_csv(f'./data/{future}.csv', index_col=0)
        df.index = pd.DatetimeIndex(df.index)
        data_df[future] = df.loc[trade_days, indicator]
    return data_df

def get_validation_data(futures:list, indicator:str) -> pd.DataFrame:
    

    data_df = pd.DataFrame(columns=futures)
    
    for future in futures:
        df = pd.read_csv(f'./data/{future}_validation.csv', index_col=0)
        df.index = pd.DatetimeIndex(df.index)
        data_df[future] = df.loc[:, indicator]
    return data_df