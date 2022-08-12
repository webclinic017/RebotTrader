from ccxtbt import CCXTStore
import backtrader as bt
from datetime import datetime, timedelta
import json
import setting
from strategy import sma_cross

cerebro = bt.Cerebro(quicknotify=True)

config = {
    'apiKey': setting.BINANCE_API_KEY,
    'secret': setting.BINANCE_SECRET_KEY,
    'timeout': 15000,
    'enableRateLimit': True,
    'verbose': True,
    'proxies': setting.VPN_PROXIES
}
store = CCXTStore(exchange='binance', currency='USDT', config=config, retries=5, debug=False, sandbox=True)


class TestStrategy(bt.Strategy):

    def __init__(self):

        self.sma = bt.indicators.SMA(self.data, period=21)

    def next(self):

        # Get cash and balance
        # New broker method that will let you get the cash and balance for
        # any wallet. It also means we can disable the getcash() and getvalue()
        # rest calls before and after next which slows things down.

        # NOTE: If you try to get the wallet balance from a wallet you have
        # never funded, a KeyError will be raised! Change LTC below as approriate
        if self.live_data:
            cash, value = self.broker.get_wallet_balance('BNB')
        else:
            # Avoid checking the balance during a backfill. Otherwise, it will
            # Slow things down.
            cash = 'NA'
            return  # 仍然处于历史数据回填阶段，不执行逻辑，返回

        for data in self.datas:
            print('{} - {} | Cash {} | O: {} H: {} L: {} C: {} V:{} SMA:{}'.format(data.datetime.datetime(),
                                                                                   data._name, cash, data.open[0],
                                                                                   data.high[0], data.low[0],
                                                                                   data.close[0], data.volume[0],
                                                                                   self.sma[0]))

    def notify_data(self, data, status, *args, **kwargs):
        dn = data._name
        dt = datetime.now()
        msg = 'Data Status: {}'.format(data._getstatusname(status))
        print(dt, dn, msg)
        if data._getstatusname(status) == 'LIVE':
            self.live_data = True
        else:
            self.live_data = False


broker_mapping = {
    'order_types': {
        bt.Order.Market: 'market',
        bt.Order.Limit: 'limit',
        bt.Order.Stop: 'stop-loss',
        bt.Order.StopLimit: 'stop limit'
    },
    'mappings': {
        'closed_order': {
            'key': 'status',
            'value': 'closed'
        },
        'canceled_order': {
            'key': 'result',
            'value': 1}
    }
}
broker = store.getbroker(broker_mapping=broker_mapping)
cerebro.setbroker(broker)

hist_start_date = datetime.utcnow() - timedelta(minutes=50)

btc = store.getdata(dataname='BTC/USDT', name="BTCUSDT",
                    timeframe=bt.TimeFrame.Minutes, fromdate=hist_start_date,
                    compression=1, ohlcv_limit=500, drop_newest=True)

eth = store.getdata(dataname='ETH/USDT', name="ETHUSDT",
                    timeframe=bt.TimeFrame.Minutes, fromdate=hist_start_date,
                    compression=1, ohlcv_limit=500, drop_newest=True)

cerebro.adddata(btc, name='btc')
cerebro.addstrategy(TestStrategy)
cerebro.addsizer(bt.sizers.PercentSizer, percents=99.999)
cerebro.run()
