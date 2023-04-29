from django.shortcuts import render
from django.http import HttpResponse
import firebase_admin
from django.contrib import messages
from firebase_admin import credentials
from firebase_admin import db
from .forms import TextInputForm, INPUTS
import time
from datetime import datetime, date


def connect_to_firebase():
    try:
        # Access Firebase Realtime DB
        cred = credentials.Certificate(
            '/Users/eiloneil/Desktop/Python/Fueler/fuelerEnv/src/config/efueler-384916-firebase-adminsdk.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://efueler-384916-default-rtdb.firebaseio.com/'
        })
    except Exception as e:
        if isinstance(e, ValueError):
            print("Already logged to FB DB. Skipping reconnection")
            pass
        else:
            raise e


def get_db_from_firebase(db_name='fuel_raw'):
    connect_to_firebase()

    # Get a reference to a specific location in the database
    ref = db.reference(f'/{db_name}')

    # Get data from the database
    return ref.get()


def calc_fuel_metrics(input_data, req):
    # get raw data
    fuel_raw = get_db_from_firebase()

    # get prev_date
    prev_date = max(list(get_all_values_from_column('Date')))

    # get last row
    prev_row = (fuel_raw[prev_date])

    # get last kms
    prev_kms = (prev_row['kms_after'])

    # calc
    try:
        diff_kms = int(float(input_data['kms']) - float(prev_kms))
        diff_days = (date.fromisoformat(
            input_data['date']) - date.fromisoformat(prev_date)).days
        price_per_l = float(input_data['cost']) / float(input_data['amount'])
        kms_per_l = diff_kms / float(input_data['amount'])
        cost_per_day = float(input_data['cost']) / diff_days

    except Exception as e:
        if isinstance(e, ZeroDivisionError):
            messages.error(req, 'Diff is zero!\nEnter different values')
            print('Diff is zero!\nEnter different values')
            return None
        else:
            raise e

    input_data.update({
        'prev_date': prev_date,
        'prev_kms': prev_kms,
        'diff_kms': diff_kms,
        'diff_days': diff_days,
        'price_per_l': round(price_per_l, 2),
        'kms_per_l': round(kms_per_l, 2),
        'cost_per_day': cost_per_day,
    })
    data = format_input_data_to_firebase(input_data)
    return data

def format_input_data_to_firebase(data):
    stg_data = {
        'amount':data['amount'],
        'cost_per_day':data['cost_per_day'],
        'diff':data['diff_kms'],
        'diff_days':data['diff_days'],
        'kms_after':data['kms'],
        'kms_before':data['prev_kms'],
        'kms_per_l':data['kms_per_l'],
        'last_date':data['prev_date'],
        'place':data['place'],
        'price_per_l':data['price_per_l'],
        'price_total':data['cost'],
    }

    final_data = {data['date'] : stg_data}
    return final_data


def push_to_db(data, db_name='fuel_raw'):
    connect_to_firebase()

    # Get a reference to a specific location in the database
    ref = db.reference(f'/{db_name}')

    # Push the data to the database
    ref.update(data)

def get_all_values_from_column(col, db_name='fuel_raw', is_ds=False):
    # get raw data
    data = get_db_from_firebase(db_name)

    if is_ds:
        return data.keys()
    else:
        try:    #  Safety measure, if a user calls for a ds (or any partition column)
                #  and forgets to tick the `is_ds` flag
            return [subset[col] for subset in data.values()]
        except:
            return data.keys()



def delete_rows_within_range(s, e, db_name='fuel_raw'):
    # get raw data
    data = get_db_from_firebase(db_name)

    # get all dates
    all_dates = data.keys()
