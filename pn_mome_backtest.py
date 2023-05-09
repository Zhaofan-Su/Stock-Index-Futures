from factor_pool import pn_mome
from utils import build_trade_days, str2datetime, get_data, get_validation_data
import pandas as pd
import numpy as np
import math
from Logger import Logger
import matplotlib.pyplot as plt


formatter = '%Y-%m-%d'
s_date = '2022-07-25'
e_date = '2022-12-30'
# s_date = '2023-01-04'
# e_date = '2023-02-28'


# 使用现货数据进行回测预测
spot_close_df = get_data(['1B0300', '1B0852'], 'close', s_date, e_date)
# 使用期货数据进行交易
future_close_df = get_data(['IF9999', 'IM9999'], 'close', s_date, e_date)
future_open_df = get_data(['IF9999', 'IM9999'], 'open', s_date, e_date)

# # 使用现货数据进行回测预测
# spot_close_df = get_validation_data(['1B0300', '1B0852'], 'close')
# # 使用期货数据进行交易
# future_close_df = get_validation_data(['IF9999', 'IM9999'], 'close')
# future_open_df = get_validation_data(['IF9999', 'IM9999'], 'open')

trade_days = spot_close_df.index
# trade_days = build_trade_days(s_date, e_date, formatter)
# 截面动量因子
period = 10
factor_values = pn_mome(spot_close_df, period)
# 因子值按行归一化
factor_values = factor_values.div(factor_values.abs().sum(axis=1), axis=0)

# 因子差异
# 为0时，不进行过滤
diff_threshold = 0.3

res_list = pd.Series(index=trade_days, dtype=float)
res_list.iloc[0] = 0

# 上个交易日开仓情况
# 0,未交易; 
# 1,多IF空IM;
# 2,空IF多IM
last_op = 0
IF_weight = 1/2
IM_weight = 1/2

# 日志
log = Logger(f'{period}D_pn_mome_threshold_{diff_threshold}')

# 交易模拟
for index in range(1, len(trade_days)):
    
    # deposit = 0.08
    deposit = 1
    commission = 0
    # commission = 0.000345 + 0.000023
    today = trade_days[index]
    log.logger.info('----------------------------------------------')
    log.logger.info(f'{today}交易开始')

    # 前一天的因子值
    previous_factor_value = factor_values.iloc[index - 1, :]

    if np.isnan(previous_factor_value['1B0300']) or np.isnan(previous_factor_value['1B0852']):
        # 不交易
        log.logger.info(f'有标的因子值为nan, 不进行交易')
        res_list[today] = 0
        last_op = 0
        log.logger.info(f'{today}交易结束, 当天总收益率为{res_list.loc[today]}')
        continue
    
    long_IF_return = (future_close_df.at[today,'IF9999'] - future_open_df.at[today, 'IF9999'])/future_open_df.at[today, 'IF9999'] 
    short_IM_return = (future_open_df.at[today,'IM9999']-future_close_df.at[today,'IM9999'])/future_open_df.at[today,'IM9999']
    long_IF_short_IM = (long_IF_return / deposit * IF_weight  
                        + short_IM_return  / deposit * IM_weight 
                        - commission)
    
    short_IF_return = (future_open_df.at[today,'IF9999'] - future_close_df.at[today, 'IF9999'])/future_open_df.at[today, 'IF9999']  
    long_IM_return = (future_close_df.at[today,'IM9999']-future_open_df.at[today,'IM9999'])/future_open_df.at[today,'IM9999']
    short_IF_long_IM = (short_IF_return /deposit * IF_weight
                        + long_IM_return /deposit * IM_weight 
                        - commission)
    
    # 两者相差小于阈值，延续上一个交易日的交易
    if abs(previous_factor_value['1B0300'] - previous_factor_value['1B0852']) < diff_threshold:
        log.logger.info(f'标的因子值相差小于阈值, 延续上个交易日的交易情况')
        if last_op == 1:
            # 上个交易日多IF空IM
            res_list[today] = long_IF_short_IM
            log.logger.info(f'多IF空IM; IF开仓{future_open_df.at[today, "IF9999"]}, IF平仓{future_close_df.at[today, "IF9999"]}, 收益率{long_IF_return}, 仓位{IF_weight}; IM开仓{future_open_df.at[today, "IM9999"]}, IM平仓{future_close_df.at[today, "IM9999"]}, 收益率{short_IM_return}, 仓位{IM_weight}.')
            log.logger.info(f'{today}交易结束, 当天总收益率为{res_list.loc[today]}')
            continue
        elif last_op == 2:
            # 上个交易日空IF多IM
            res_list[today] = short_IF_long_IM
            log.logger.info(f'空IF多IM; IF开仓{future_open_df.at[today, "IF9999"]}, IF平仓{future_close_df.at[today, "IF9999"]}, 收益率{short_IF_return}, 仓位{IF_weight}; IM开仓{future_open_df.at[today, "IM9999"]}, IM平仓{future_close_df.at[today, "IM9999"]}, 收益率{long_IM_return}, 仓位{IM_weight};')
            log.logger.info(f'{today}交易结束, 当天总收益率为{res_list.loc[today]}')
            continue

    log.logger.info(f'标的因子值相差大于阈值, 进行新交易')
    if previous_factor_value['1B0300'] >= previous_factor_value['1B0852']:
        # 多IF，空IM
        # 均仓
        # 保证金8%
        res_list[today] = long_IF_short_IM
        log.logger.info(f'多IF空IM; IF开仓{future_open_df.at[today, "IF9999"]}, IF平仓{future_close_df.at[today, "IF9999"]}, 收益率{long_IF_return}, 仓位{IF_weight}; IM开仓{future_open_df.at[today, "IM9999"]}, IM平仓{future_close_df.at[today, "IM9999"]}, 收益率{short_IM_return}, 仓位{IM_weight}.')
        last_op = 1
    elif previous_factor_value['1B0300'] < previous_factor_value['1B0852']:
        # 空IF，多IM
        # 均仓
        res_list[today] = short_IF_long_IM
        log.logger.info(f'空IF多IM; IF开仓{future_open_df.at[today, "IF9999"]}, IF平仓{future_close_df.at[today, "IF9999"]}, 收益率{short_IF_return}, 仓位{IF_weight}; IM开仓{future_open_df.at[today, "IM9999"]}, IM平仓{future_close_df.at[today, "IM9999"]}, 收益率{long_IM_return}, 仓位{IM_weight};')
        last_op = 2

    log.logger.info(f'{today}交易结束, 当天总收益率为{res_list.loc[today]}')

# 沪深300指数、中证1000收益率
idx_return = spot_close_df.apply(lambda x: np.log(x).diff(1), axis=0)

# plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['font.sans-serif']= ['Heiti TC']#防止中文乱码
plt.rcParams['axes.unicode_minus']=False

plt.figure(figsize=(12,8))
# plt.rcParams['font.sans-serif'] = ['SimHei']  # 显示汉字
plt.xlabel('date')  # x轴标题
plt.ylabel('return')  # y轴标题
plt.plot(trade_days, res_list.cumsum(), c='r', label='strategy')
plt.plot(trade_days, idx_return['1B0300'].cumsum(), c='g', label='1B0300')
plt.plot(trade_days, idx_return['1B0852'].cumsum(), c='b', label='1B0852')
plt.legend()
fig_title = f'{period}天截面动量因子-等权-现货预测-期货交易-阈值{diff_threshold}'
plt.title(fig_title)
plt.savefig(f'./figs/{fig_title}.png')
plt.show()
