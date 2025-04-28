import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.pyplot import MultipleLocator

def read_xls_files(files) -> list[pd.DataFrame]:
    df_list = []
    for file in files:
        df_list.append(pd.read_excel(file))
    return df_list

def pop_row(df: pd.DataFrame) -> (pd.DataFrame, pd.Series):
    row = df.iloc[0]
    df = df.iloc[1:]
    return df, row


def execute(files_and_target_ratios: dict, start_date: str, end_date: str, cycle: int, debug=False):
    '''
    :param files: xls文件列表和持仓比例（dict）
    :param target_ratio: 目标持仓比例
    :param start_date: 回测起始日期(yyyy.mm.dd)
    :param end_date: 回测终止日期(yyyy.mm.dd)
    :param cycle: 调仓周期(天)
    :return:
    '''
    money = 1000000
    df_list = read_xls_files(files_and_target_ratios.keys())
    target_ratio = list(files_and_target_ratios.values())

    data_each_day = [[start_date]] # 日期、所有持仓、总额
    for i in range(len(target_ratio)):
        data_each_day[0].append(money * target_ratio[i])
    data_each_day[0].append(sum(data_each_day[0][1:]))
    cur_day = start_date

    cur_price = []
    date_and_price_list = []

    for df in df_list:
        # row = df.iloc[0]
        # while df.iloc[0]['日期'] <= cur_day:
        #     df, row = pop_row(df)
        # cur_price.append(row['累计净值'])
        date_and_price = []
        for idx, row in df.iterrows():
            date_and_price.append([row['日期'], row['累计净值']])
        date_and_price_list.append(date_and_price)

    for i in range(len(date_and_price_list)):
        date_and_price = date_and_price_list[i]
        row = date_and_price[0]
        while date_and_price[0][0] <= cur_day:
            row = date_and_price[0]
            date_and_price = date_and_price[1:]
            if len(date_and_price) == 0:
                break
        if len(date_and_price) == 0:
            break
        cur_price.append(row[1])

    start_timestamp = pd.Timestamp(start_date).timestamp()
    now_timestamp = pd.Timestamp.now().timestamp()
    rebalance_date_list = [] # 调仓日列表
    while start_timestamp < now_timestamp:
        # start_timestamp转化为"yyyy.mm.dd"格式
        cur_date = pd.to_datetime(start_timestamp, unit='s').strftime("%Y.%m.%d")
        rebalance_date_list.append(cur_date)
        start_timestamp += cycle * 24 * 60 * 60

    while cur_day < end_date:

        today_money = []
        for i in range(len(date_and_price_list)):
            df = date_and_price_list[i]
            row = df[0]
            while df[0][0] <= cur_day:
                row = df[0]
                df = df[1:]
                if len(df) == 0:
                    break
            if len(df) == 0:
                break
            now_price = row[1]
            last_money = data_each_day[-1][i + 1]
            cur_money = last_money * now_price / cur_price[i]
            today_money.append(float(cur_money))
            cur_price[i] = now_price
        if len(df) == 0:
            break

        # 判断是否要调仓
        if cur_day in rebalance_date_list:
            all_money = sum(today_money)
            for i in range(len(target_ratio)):
                today_money[i] = all_money * target_ratio[i]

        data_this_day = [cur_day]
        for m in today_money:
            data_this_day.append(m)
        data_this_day.append(sum(today_money))
        data_each_day.append(data_this_day)
        if debug:
            print(cur_day)
            print(data_this_day)

        cur_timestamp = pd.Timestamp(cur_day).timestamp()
        cur_timestamp += 24 * 60 * 60
        cur_day = pd.to_datetime(cur_timestamp, unit='s').strftime("%Y.%m.%d")

    return data_each_day[1:] # 去掉dummy头部


def cal_yearly_rate(date_money: list[(str, float)]) -> float:
    '''
    计算年化收益率
    :param date_money:
    :return: 年化收益率
    '''
    yearly_rate = ((date_money[-1][1] / date_money[0][1]) ** (365 / len(date_money))) - 1
    return yearly_rate


def cal_max_recall(date_money: list[(str, float)]) -> float:
    '''
    计算最大回撤
    :param date_money:
    :return: 最大回撤
    '''
    cur_max = []
    cur_recall = []
    for item in date_money:
        if len(cur_max) == 0 or item[1] > cur_max[-1][1]:
            cur_max.append(item)
        else:
            cur_max.append(cur_max[-1])
        cur_recall.append(1 - item[1] / cur_max[-1][1])
    max_recall = max(cur_recall)
    idx = cur_recall.index(max_recall)
    print(f"最大回撤发生于{date_money[idx][0]}，当前最大值{cur_max[idx][1]}，当前金钱{date_money[idx][1]}，回撤{cur_recall[idx]}")
    return max_recall

def cal_longest_recall(date_money: list[(str, float)]) -> list[str, int]:
    longest_recall = []
    cur_longest = 0
    cur_max = []
    for item in date_money:
        if len(cur_max) == 0 or item[1] > cur_max[-1][1]:
            cur_max.append(item)
        else:
            cur_max.append(cur_max[-1])
        if item[1] < cur_max[-1][1]:
            cur_longest += 1
        else:
            if len(longest_recall) == 0 or cur_longest > longest_recall[1]:
                longest_recall = [item[0], cur_longest]
            cur_longest = 0
    return longest_recall


def plot_profit(date_money: list[(str, float)]):
    '''
    绘制净值曲线
    :param date_money:
    :return:
    '''
    plt.figure(figsize=(15, 7), dpi=100)
    plt.ylabel('Profit')
    plt.xlabel('Date')
    x_major_locator = MultipleLocator(int(len(date_money) / 15))
    ax = plt.gca()
    ax.xaxis.set_major_locator(x_major_locator)
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.plot([row[0] for row in date_money], [row[1]/date_money[0][1] for row in date_money])
    plt.show()


if __name__ == '__main__':
    start_timestamp = pd.Timestamp('2022.08.09').timestamp()
    end_timestamp = pd.Timestamp('2025.4.20').timestamp()
    shortest_days = 180 # 最短持有
    while start_timestamp < end_timestamp - shortest_days * 24 * 60 * 60:
        start_test_date = pd.to_datetime(start_timestamp, unit='s').strftime("%Y.%m.%d")
        end_test_date = pd.to_datetime(end_timestamp, unit='s').strftime("%Y.%m.%d")
        print(f'开始测试，买入日期：{start_test_date} ===============')
        data_each_day = execute(
            {
                # "./511520.xls": 1, # 债
                "./000055.xls": 1, # 纳指
                # "./008114.xls": 0.5,  # 红利
             }, start_test_date, end_test_date, 30
        )
        date_money = []
        for row in data_each_day:
            date_money.append((row[0], row[-1]))

        # 计算年化收益率
        # R = (1 + P) ^ (m / n) - 1
        # 1 + P = 末期资产/初期资产，m = 365, n = 执行天数
        yearly_rate = cal_yearly_rate(date_money)
        print(f'年化{yearly_rate*100}%')

        # 计算波动率

        # 计算最大回撤
        max_recall = cal_max_recall(date_money)

        # 计算最长回撤
        longest_recall = cal_longest_recall(date_money)
        print(f'最长回撤终止日{longest_recall[0]}, 持续时间{longest_recall[1]}')

        # 计算夏普比率？（无风险利率如何获取）

        # 绘制净值曲线
        # plot_profit(date_money)

        print("end")
        start_timestamp += 24 * 60 * 60 * 30
