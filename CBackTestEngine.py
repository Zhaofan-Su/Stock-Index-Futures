import pandas as pd
import numpy as np
import math

from datetime import datetime, timedelta
from utils import str2datetime, build_trade_days

# 日志
from Logger import Logger

class CBackTestEngine(object):

    def __init__(self, sdate, edate, log_name='all', commission=False,  leverage=False, portfolio_cash=10000000) -> None:
        self.log = Logger(log_name, level='debug')

        # self.sdate = str2datetime(sdate)
        # self.edate = str2datetime(edate)
        self.sdate = sdate
        self.edate = edate


        # 初始化账户信息及持仓
        self.init_portofolio(portfolio_cash)
        # 是否使用杠杆
        self.leverage = leverage
        # 是否使用手续费
        self.commission = commission
        # 交易品种
        self.future_dic = {'1B0300':'IF9999', '1B0852':'IM9999'}
        self.futures = ['IF9999', 'IM9999']
        self.spots = ['1B0300', '1B0852']
        # # 交易日列表
        # self.trade_days = build_trade_days(sdate, edate)
        # universe mask
        # self.universe_mask = self.make_universe_mask()
        # self.log.logger.info('Prepare the target future pool for each trade day succcessfully!')

        self.log.logger.info('The back test engine set successfully!')
        pass

    def init_portofolio(self, portfolio_cash=10000000) -> None:
        """ 初始化账户信息及持仓
        """
        # 账户情况
        self.portfolio = {}
        self.portfolio['cash'] = portfolio_cash
        # 头寸
        self.position = {}
        self.log.logger.info('Init the portfolio and position detail successfully!')
        return

    def open_position(self, future_list: list) -> float:
        """ 开仓

        Args:
            future_list (list): 要开仓的品种的详情列表
        Returns:
            float: 开仓花费
        """
        cost = 0
        for future_detail in future_list:
            # 品种名称
            future = future_detail['future']

            # 计算手续费
            if self.commission == False:
                commission = 0
            else:
                # 开仓手续费为万分之0.23
                commission = 0.000023

            # 加进持仓
            self.position[f'{future}'] = future_detail
            if future_detail["direction"] == 'long':
                self.log.logger.info(f'做多{future}, 开仓价格{future_detail["price"]}, 仓位{future_detail["weight"]}')
            else:
                self.log.logger.info(f'做空{future}, 开仓价格{future_detail["price"]}, 仓位{future_detail["weight"]}')
           
            # 计算开仓手续费
            cost += commission * future_detail['weight']

        return cost

    def close_position(self, close_data: pd.Series, today=True) -> float:
        """ 平掉所有仓位

        Args:
            close_data (pd.Series): 品种的平仓价格
            today (bool): 是否为平今仓
        Returns:
            float: 平仓收益率
        """
        # 平仓计算价格
        all_return = 0
        for holding in self.position.keys():
            holding_detail = self.position[holding]
            deposit = 0.08 if self.leverage else 1
            # 计算手续费
            if today:
                # 平今仓
                commission = 0.000345 * holding_detail['weight']
            else:
                commission = 0.000023 * holding_detail['weight']
            if self.commission == False:
                commission = 0
            ret = 0
            if holding_detail['direction'] == 'long':
                # 多头持仓
                ret = (close_data[holding] - holding_detail['price']) / holding_detail['price'] / deposit * holding_detail['weight']
                self.log.logger.info(f'平{holding}多头, 平仓价格{close_data[holding]}, 平仓收益{ret}, 平仓手续费{commission}')
            elif holding_detail['direction'] == 'short':
                # 空头持仓
                ret = (holding_detail['price'] - close_data[holding]) / holding_detail['price'] / deposit * holding_detail['weight']
                self.log.logger.info(f'平{holding}空头, 平仓价格{close_data[holding]}, 平仓收益{ret}, 平仓手续费{commission}')


            # 计算平仓收益率
            all_return -= commission
            all_return += ret

        # 清空持仓
        self.position = {}
        return all_return

    def get_data(self, futures:list, indicator:str, s_date:str, e_date:str) -> pd.DataFrame:
        """ 获取品种数据

        Args:
            futures (list): _description_
            indicator (str): 数据指标
            s_date (str): _description_
            e_date (str): _description_

        Returns:
            pd.DataFrame: _description_
        """
        # trade_days = build_trade_days(s_date, e_date)

        data_df = pd.DataFrame(columns=futures)

        for future in futures:
            df = pd.read_csv(f'./data/{future}.csv', index_col=0)
            df.index = pd.DatetimeIndex(df.index)
            temp = df[s_date: e_date]
            data_df[future] = temp[indicator]
        return data_df
    
    def trade_T_1(self, factor_signs:pd.DataFrame)-> pd.Series:
        """ T日早盘开仓, T+1日早盘平仓

        Args:
            factor_signs (pd.DataFrame): 因子信号，代表因子权重及开仓方向

        Returns:
            pd.Series: _description_
        """
        res_list = pd.Series(index=factor_signs.index[1:-1], dtype=float)

        # 期货开盘价
        open_df = self.get_data(self.futures, 'open', self.sdate, self.edate)
        
        # T日早盘开仓，T+1日早盘平仓
        for index in range(1, len(factor_signs)-1):
            ret = 0
            # T日
            today = factor_signs.index[index]
            self.log.logger.info('----------------------------------------------')
            self.log.logger.info(f'{today}交易开始')

            # 前一天的因子信号
            previous_factor_value = factor_signs.iloc[index - 1, :]

            # 平仓收益, 平昨仓
            close_ret = self.close_position(open_df.iloc[index, :], False)

            if np.isnan(previous_factor_value['1B0300']) or np.isnan(previous_factor_value['1B0852']):
                # 不交易
                self.log.logger.info(f'有标的因子值为nan, 不开仓')
                res_list.at[today] += close_ret
                self.log.logger.info(f'{today}交易结束, 当天总收益率为{res_list.at[today]}')
                continue

            # 开仓详情
            open_list = []
            for spot in previous_factor_value.index:
                open_detail = {}
                future = self.future_dic[spot]
                open_detail['future'] = future
                open_detail['price'] = open_df.at[today, future]
                if previous_factor_value[spot] > 0:
                    # 多头
                    open_detail['direction'] = 'long'
                    open_detail['weight'] = previous_factor_value[spot]
                else:
                    # 空头
                    open_detail['direction'] = 'short'
                    open_detail['weight'] = abs(previous_factor_value[spot])
                open_list.append(open_detail)
            
            # 开仓成本
            open_cost = self.open_position(open_list)

            # 当天总收益
            res_list.at[today] = close_ret - open_cost
            self.log.logger.info(f'{today}交易结束, 当天总收益率为{res_list.at[today]}')
        
         # 年化收益率
        ret_y = res_list.mean() * 252
        self.log.logger.info(f'年化收益率是{ret_y}')
        # 波动率
        volatility = res_list.std() * np.sqrt(252)
        self.log.logger.info(f'年化波动率是{volatility}')
        # 夏普比率
        sharp = (ret_y - 0.0214) / volatility
        self.log.logger.info(f'年化夏普比率是{sharp}.')

        return res_list

    def trade_T(self, factor_signs:pd.DataFrame)-> pd.Series:
        """ T日早盘开仓, T日尾盘平仓

        Args:
            factor_signs (pd.DataFrame): 因子信号，代表因子权重及开仓方向

        Returns:
            pd.Series: _description_
        """
        res_list = pd.Series(index=factor_signs.index[1:], dtype=float)

        # 期货收盘价
        close_df = self.get_data(self.futures, 'close', self.sdate, self.edate)
        # 期货开盘价
        open_df = self.get_data(self.futures, 'open', self.sdate, self.edate)
        
        # T日早盘开仓，T日尾盘平仓
        for index in range(1, len(factor_signs)):
            ret = 0
            # T日
            today = factor_signs.index[index]
            self.log.logger.info('----------------------------------------------')
            self.log.logger.info(f'{today}交易开始')

            # 前一天的因子信号
            previous_factor_value = factor_signs.iloc[index - 1, :]

            if np.isnan(previous_factor_value['1B0300']) or np.isnan(previous_factor_value['1B0852']):
                # 不交易
                self.log.logger.info(f'有标的因子值为nan, 不开仓')
                res_list.at[today] = 0
                self.log.logger.info(f'{today}交易结束, 当天总收益率为{res_list.at[today]}')
                continue

            # 开仓详情
            open_list = []
            for spot in previous_factor_value.index:
                open_detail = {}
                future = self.future_dic[spot]
                open_detail['future'] = future
                open_detail['price'] = open_df.at[today, future]
                if previous_factor_value[spot] > 0:
                    # 多头
                    open_detail['direction'] = 'long'
                    open_detail['weight'] = previous_factor_value[spot]
                else:
                    # 空头
                    open_detail['direction'] = 'short'
                    open_detail['weight'] = abs(previous_factor_value[spot])
                open_list.append(open_detail)
            
            # 开仓成本
            open_cost = self.open_position(open_list)

            # 平仓收益, 平今仓
            close_ret = self.close_position(close_df.iloc[index, :], True)

            # 当天总收益
            res_list.at[today] = close_ret - open_cost
            self.log.logger.info(f'{today}交易结束, 当天总收益率为{res_list.at[today]}')
        
        # 年化收益率
        ret_y = res_list.mean() * 252
        self.log.logger.info(f'年化收益率是{ret_y}')
        # 波动率
        volatility = res_list.std() * np.sqrt(252)
        self.log.logger.info(f'年化波动率是{volatility}')
        # 夏普比率
        sharp = (ret_y - 0.0214) / volatility
        self.log.logger.info(f'年化夏普比率是{sharp}.')

        return res_list


   