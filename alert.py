from alpha_vantage.timeseries import TimeSeries
from email.message import EmailMessage
import pandas as pd
import numpy as np
import smtplib
import time

'''Module that will be used to send out market alerts'''
class Alert:

    def __init__(self, symbol=None, alert=None, logic=None, interval='daily', contacts=['YOUR CONTACT(S) HERE']):
        self.symbol = symbol
        self.alert = alert
        self.logic = logic
        self.contacts = contacts
        self.interval = interval
        self.ts = TimeSeries(key='YOUR API KEY HERE', output_format='pandas')
        self.ma1 = 10
        self.ma2 = 20
        self.ma3 = 50
        self.target = None
        self.percent = None
        self.get_data()


    # review this method (might scrap)
    def set_logic_params(self, **kwargs):
        '''Manage params for logic'''
        self.ma1 = kwargs['ma1']
        self.ma2 = kwargs['ma2']
        self.ma3 = kwargs['ma3']
        self.target = kwargs['target']
        self.percent = kwargs['percent']


    def get_data(self):
        '''get data, duh'''
        if self.interval == 'daily':
            data, metadata = self.ts.get_daily(symbol=self.symbol, outputsize='full')
        elif self.interval == 'weekly':
            data, metadata = self.ts.get_weekly(symbol=self.symbol)

        data.columns = ['open', 'high', 'low', 'close', 'volume']
        self.data = data.iloc[::-1].tail(200)
        print(self.data)


    def update(self):
        '''Alert Logic'''
        if self.logic == 'MA Crossover':
            update = self.ma_cross(self.data)
            if update == True:
                self.send()

        elif self.logic == 'MACD Crossover':
            update = self.macd(self.data)
            if update == True:
                self.send()

        elif self.logic == 'Price':
            update = self.price_target(self.data)
            if update == True:
                self.send()

        elif self.logic == 'Percent':
            update = self.pct_movement(self.data)
            if update == True:
                self.send()

        else:
            print('Error, please set logic with .set_logic(logic=str)')


    def ma_cross(self, data):
        '''Control MA Strategy'''
        data['returns'] = data.loc[:, 'close'].pct_change()
        data['ma1'] = data['close'].rolling(self.ma1).mean()
        data['ma2'] = data['close'].rolling(self.ma2).mean()
        data['ma3'] = data['close'].rolling(self.ma3).mean()
        data['cross1'] = np.where(data['ma1'] > data['ma2'], 1, -1)
        data['cross2'] = np.where(data['ma1'] > data['ma3'], 0, -0)
        data['signal'] = data['cross1'] + data['cross2']
        
        if data.iloc[-1, -1] != data.iloc[-2, -1]:
            if iloc[-1, -1] == 1:
                self.trend = 'bullish'
            else: 
                self.trend = 'bearish'
            return True
        else: 
            return False


    def macd(self, data):
        '''Control MACD Strategy'''
        data['returns'] = data.loc[:, 'close'].pct_change()
        data['ma1'] = data['close'].rolling(self.ma1).mean()
        data['ma2'] = data['close'].rolling(self.ma2).mean()
        data['macd'] = data['ma1'] - data['ma2']
        data['signal'] = np.where(data['macd'] > 0, 1, -1)

        if data.iloc[-1, -1] != data.iloc[-2, -1]:
            if data.iloc[-1, -1] == 1:
                self.trend = 'bullish'
            else:
                self.trend = 'bearish'
            return True
        else:
            return False


    def pos_movement(self, data):
        '''Control position update alerts'''
        pass


    def price_target(self, data):
        '''Control price target alerts'''
        if data.iloc[-2, 3] <= self.target and self.target <= data.iloc[-1, 3]:
            self.where = 'above'
            return True
        elif data.iloc[-2, 3] >= self.target and self.target >= data.iloc[-1, 3]:
            self.where = 'below'
            return True
        else:
            return False


    def send(self):
        '''Send Alert'''
        msg = EmailMessage()

        user = 'YOUR EMAIL HERE'
        msg['from'] = user
        password = 'YOUR GOOGLE APP PASSWORD HERE'
        if self.alert != None:
            msg['subject'] = f"{self.alert.title()} Alert"
        else:
            msg['subject'] = "Alert"

        if self.alert == 'signal':
            body = f"{self.symbol.upper()} showing {self.trend} {self.logic}"
        if self.alert == 'position':
            body = f"You are {self.direction} {self.percent}% on {self.symbol.upper()}."
        if self.alert == 'price':
            body = f"{self.symbol} is {self.where} ${self.target}"


        msg.set_content(body)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, password)

        for contact in self.contacts:
            msg['to'] = contact
            server.send_message(msg)

        server.quit()
        print('Message Sent!')


    def run(self, sec):
        '''Create loop to run alert'''
        while True:
            self.update()
            time.sleep(sec)
