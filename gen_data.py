import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 设置随机种子，保证每次生成的数据一样
np.random.seed(42)

# 生成 2026 年 1 月 1 日到 2026 年 6 月 30 日的数据
start_date = datetime(2026, 1, 1)
dates = [start_date + timedelta(days=x) for x in range(180)]

channels = ['DTC', 'Amazon', 'TikTok', 'Store']
categories = ['Blind Box', 'Plush', 'Action Figure', 'Accessories']
data = []

for i, date in enumerate(dates):
    # 模拟周末流量上涨（周末系数）
    weekend_boost = 1.5 if date.weekday() >= 5 else 1.0

    for channel in channels:
        for cat in categories:
            # 基础流量模拟
            base_traffic = {'DTC': 3000, 'Amazon': 5000, 'TikTok': 8000, 'Store': 500}[channel]
            traffic = int(base_traffic * weekend_boost * np.random.uniform(0.8, 1.2))

            # 基础转化率模拟（TikTok流量大但转化低，Store转化高）
            base_cvr = {'DTC': 0.03, 'Amazon': 0.04, 'TikTok': 0.015, 'Store': 0.08}[channel]
            cvr = base_cvr * np.random.uniform(0.8, 1.2)
            orders = int(traffic * cvr)

            # 客单价模拟
            atv = np.random.uniform(30, 100)
            sales = round(orders * atv, 2)

            # 成本（如果是电商，可以理解为广告费+产品成本；这里设为销售额的 60%-80%）
            cost = round(sales * np.random.uniform(0.6, 0.8), 2)

            data.append([date.strftime('%Y-%m-%d'), channel, cat, traffic, orders, sales, cost])

df = pd.DataFrame(data, columns=['Date', 'Channel', 'Category', 'Traffic', 'Orders', 'Sales', 'Cost'])

# 保存为 CSV
df.to_csv('popmart_sales_data.csv', index=False)
print("✅ 完美数据集生成完毕：popmart_sales_data.csv，共", len(df), "行数据")
