import pandas as pd
from utils import build_trade_days

s_date = '20221101'
e_date = '20221230'

trade_days = build_trade_days(s_date, e_date, '%Y%m%d')

open_data_df = pd.DataFrame(index=trade_days, columns=['IC','IM'])
close_data_df = pd.DataFrame(index=trade_days, columns=['IC','IM'])
for day in trade_days:
    days_str = day.strftime('%Y%m%d')
    IC_data = pd.read_csv(f"./CFFEX/{days_str}/IC主力连续_{days_str}.csv", encoding='gb2312', index_col=0)
    IM_data = pd.read_csv(f"./CFFEX/{days_str}/IM主力连续_{days_str}.csv", encoding='gb2312', index_col=0)
    open_data_df.at[day, 'IC'] = IC_data.iat[0,2]
    open_data_df.at[day, 'IM'] = IM_data.iat[0,2]
    close_data_df.at[day, 'IC'] = IC_data.iat[len(IC_data)-1, 2]
    close_data_df.at[day, 'IM'] = IM_data.iat[len(IM_data)-1, 2]

open_data_df.to_csv('./data/open_data.csv')
close_data_df.to_csv('./data/close_data.csv') 




