import pandas as pd

def read_xls_files(files) -> list[pd.DataFrame]:
    df_list = []
    for file in files:
        df_list.append(pd.read_excel(file))
    return df_list

def pop_row(df: pd.DataFrame) -> (pd.DataFrame, pd.Series):
    row = df.iloc[0]
    df = df.iloc[1:]
    return df, row

def execute(files_and_target_ratios: dict, start_date: str, end_date: str, cycle: int):
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
    for df in df_list:
        row = df.iloc[0]
        while df.iloc[0]['日期'] <= cur_day:
            df, row = pop_row(df)
        cur_price.append(row['累计净值'])

    start_timestamp = pd.Timestamp(start_date).timestamp()
    now_timestamp = pd.Timestamp.now().timestamp()
    rebalance_date_list = [] # 调仓日列表
    while start_timestamp < now_timestamp:
        # start_timestamp转化为"yyyy.mm.dd"格式
        cur_date = pd.to_datetime(start_timestamp, unit='s').strftime("%Y.%m.%d")
        rebalance_date_list.append(cur_date)
        start_timestamp += cycle * 24 * 60 * 60

    while cur_day < end_date:
        print(cur_day)
        today_money = []
        for i in range(len(df_list)):
            df = df_list[i]
            row = df.iloc[0]
            while df.iloc[0]['日期'] <= cur_day:
                df, row = pop_row(df)
                if df.empty:
                    break
            if df.empty:
                break
            now_price = row['累计净值']
            last_money = data_each_day[-1][i + 1]
            cur_money = last_money * now_price / cur_price[i]
            today_money.append(float(cur_money))
            cur_price[i] = now_price
        if df.empty:
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
        print(data_this_day)

        cur_timestamp = pd.Timestamp(cur_day).timestamp()
        cur_timestamp += 24 * 60 * 60
        cur_day = pd.to_datetime(cur_timestamp, unit='s').strftime("%Y.%m.%d")

    return data_each_day[1:] # 去掉dummy头部


if __name__ == '__main__':
    data_each_day = execute(
        {"./511520.xls": 0.3,
         "./000055.xls": 0.2,
         "./512890.xls": 0.5,
         }, "2024.12.14", "2025.4.20", 30
    )
    money = []
    for row in data_each_day:
        money.append(row[-1])
    # 计算年化收益率
    # R = (1 + P) ^ (m / n) - 1
    # 1 + P = 末期资产/初期资产，m = 365, n = 执行天数

    # 计算波动率

    # 计算最大回撤

    # 计算最长回撤

    # 计算夏普比率？（无风险利率如何获取）
