from factor_pool import pn_mome, ts_mome
from CBackTestEngine import CBackTestEngine
import numpy as np

import matplotlib.pyplot as plt
if __name__ == '__main__':
    # 样本内
    s_date = '2022-07-25'
    e_date = '2022-12-30'
    # 样本外
    # s_date = '2023-01-04'
    # e_date = '2023-02-28'

    period = 3
    threshold = 0.2

    # filename = f'样本外补充实验-截面动量因子-{period}天-阈值{threshold}-因子值加权'
    filename = 'test'
    bt_engine = CBackTestEngine(s_date, e_date, filename)
    
    # 指数现货数据
    spot_close_df = bt_engine.get_data(['1B0300', '1B0852'], 'close', s_date, e_date)
    factor_signs = pn_mome(spot_close_df, period, threshold)

    # 回测
    res_list = bt_engine.trade_T(factor_signs)


    # 沪深300指数、中证1000指数收益率
    
    idx_return = spot_close_df.apply(lambda x: np.log(x).diff(1), axis=0)
    idx_return = idx_return.loc[res_list.index,:]

    # plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['font.sans-serif']= ['Heiti TC']#防止中文乱码
    plt.rcParams['axes.unicode_minus']=False

    plt.figure(figsize=(12,8))
    # plt.rcParams['font.sans-serif'] = ['SimHei']  # 显示汉字
    plt.xlabel('date')  # x轴标题
    plt.ylabel('return')  # y轴标题
    plt.plot(res_list.index, res_list.cumsum(), c='r', label='strategy')
    plt.plot(res_list.index, idx_return['1B0300'].cumsum(), c='g', label='1B0300')
    plt.plot(res_list.index, idx_return['1B0852'].cumsum(), c='b', label='1B0852')
    plt.legend()
    plt.title(filename)
    plt.savefig(f'./figs/trade_nextday/{filename}.png')
    plt.show()
