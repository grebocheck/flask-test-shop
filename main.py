# -*- coding: utf-8 -*-
from flask import Flask, render_template, request  # ,redirect ,url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from logger import log
import settings
import requests
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    currency = db.Column(db.String(10), nullable=False)
    value = db.Column(db.Float(1000), nullable=False)
    time_create = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '<Payment %r>' % self.id


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/pay', methods=['POST'])
def pay():
    currency = request.form['currency']
    value = float(request.form['value'])
    description = request.form['description']

    # print(f"Currency: {currency}")
    # print(f"Value: {value}")
    # print(f"Description: {description}")

    payment = Payment(currency=currency,
                      value=value,
                      description=description,
                      time_create=datetime.now())

    try:
        db.session.add(payment)
        db.session.commit()

        # currency_code, value, description, shop_id

        if currency == 'EUR':
            currency_code = 978  # code EUR
            pre_hash_1 = f"{value}:{currency_code}:{settings.shop_id}:{payment.id}{settings.secretKey}"
            hex_dig = hashlib.sha256(pre_hash_1.encode()).hexdigest()
            return render_template('pay1.html',
                                   value=value,
                                   currency=currency_code,
                                   shop_id=settings.shop_id,
                                   description=description,
                                   payment_id=payment.id,
                                   hex_dig=hex_dig)
        elif currency == 'USD':
            currency_code = 840  # code USD
            shop_currency = 643  # code for shop (RUB)
            url = 'https://core.piastrix.com/bill/create'
            pre_hash_2 = f"{currency_code}:{value}:{shop_currency}:{settings.shop_id}:{payment.id}{settings.secretKey}"
            hex_dig = hashlib.sha256(pre_hash_2.encode()).hexdigest()
            data = {
                "description": description,
                "payer_currency": currency_code,
                "shop_amount": str(value),
                "shop_currency": shop_currency,
                "shop_id": settings.shop_id,
                "shop_order_id": payment.id,
                "sign": hex_dig
            }

            x = requests.post(url, json=data)

            # print(x.text)

            return str(x.text)
        elif currency == 'RUB':
            currency_code = 643  # code RUB
            url = 'https://core.piastrix.com/invoice/create'
            pre_hash_2 = f"{value}:{currency_code}:{settings.payway}:{settings.shop_id}:{payment.id}{settings.secretKey}"
            hex_dig = hashlib.sha256(pre_hash_2.encode()).hexdigest()
            data = {
                'amount': value,
                'currency': currency_code,
                'payway': settings.payway,
                'shop_id': settings.shop_id,
                "shop_order_id": payment.id,
                "sign": hex_dig
            }

            x = requests.post(url, json=data)

            print(x.json())

            return render_template('pay3.html',
                                   id=x.json()['data']['id'],
                                   method=x.json()['data']['method'],
                                   url=x.json()['data']['url'],
                                   ac_account_email=x.json()['data']['data']['ac_account_email'],
                                   ac_sci_name=x.json()['data']['data']['ac_sci_name'],
                                   ac_amount=x.json()['data']['data']['ac_amount'],
                                   ac_currency=x.json()['data']['data']['ac_currency'],
                                   ac_order_id=x.json()['data']['data']['ac_order_id'],
                                   ac_sub_merchant_url=x.json()['data']['data']['ac_sub_merchant_url'],
                                   ac_sign=x.json()['data']['data']['ac_sign'])
        else:
            log("Ошибка связаная с выбором валюты")

    except Exception as e:
        log(e)
        return "При добавлении обнаружилась ошибка."


@app.route('/payments/')
def payments():
    payments = Payment.query.order_by(Payment.time_create.desc()).all()
    return render_template('payments.html', payments=payments)


if __name__ == '__main__':
    log("Запуск")
    app.run(debug=True)
