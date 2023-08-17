from django.shortcuts import render
from django.http import HttpResponse
import firebase_admin
from django.contrib import messages
from firebase_admin import credentials
from firebase_admin import db
from .forms import TextInputForm, INPUTS
import time
from datetime import datetime, date, time
# import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Create a connection to FireBase DB
cred = credentials.Certificate(
    os.path.join(BASE_DIR, 'config/efueler-384916-firebase-adminsdk.json'))

FIREBASE_CONNECTION = firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://efueler-384916-default-rtdb.firebaseio.com/'
})


def get_db_from_firebase(db_name='fuel_raw'):
    # Get a reference to a specific location in the database
    ref = db.reference(f'/{db_name}')

    # Get data from the database
    return ref.get()


# get last row function:
def get_last_row_from_db(db_name='fuel_raw'):
    fuel_raw = get_db_from_firebase()
    prev_date = max(list(get_all_values_from_column('Date', is_ds=True)))

    # get last row
    return prev_date, fuel_raw[prev_date]


def calc_fuel_metrics(input_data, req):
    cost = float(input_data['cost'])
    amount = float(input_data['amount'])
    kms = float(input_data['kms'])

    # get raw data
    fuel_raw = get_db_from_firebase()

    # get last row
    prev_date, prev_row = get_last_row_from_db()

    # get last kms
    prev_kms = (prev_row['kms_after'])

    # calc
    try:
        diff_kms = int(kms - float(prev_kms))
        diff_days = int((date.fromisoformat(
            input_data['date']) - date.fromisoformat(prev_date)).days)
        price_per_l = cost / amount
        kms_per_l = diff_kms / amount
        cost_per_day = cost / diff_days
        kms_per_day = diff_kms / diff_days
        if diff_kms < 1:
            raise ZeroDivisionError("Too small a Km diff")

    except Exception as e:
        if isinstance(e, ZeroDivisionError):
            messages.error(req, 'Diff is zero!\nEnter different values')
            print('Diff is zero!\nEnter different values')
            return None
        else:
            raise e

    # Calc rolling values
    cols = ['diff',
            'diff_days',
            'amount',
            'price_total']
    total_values = {}
    for col in cols:
        try:
            # calculate the sum of each column, in order to calculate the rolling values
            vals = sum(get_all_values_from_column(col, is_ds=False))
            total_values[col] = vals
        except Exception as e:
            print("=====/=/=/==/======")
            print(f'Is Error a TypeError:{isinstance(e, TypeError)}')
            print(col)
            print(get_all_values_from_column(col, is_ds=False))
            print("=====/=/=/==/======")
    print(total_values)

    rolling_cost_per_day = (total_values['price_total'] + cost) / (total_values['diff_days'] + diff_days)
    rolling_kms_per_l = (total_values['diff'] + diff_kms) / (total_values['amount'] + amount)
    rolling_kms_per_day = (total_values['diff'] + diff_kms) / (total_values['diff_days'] + diff_days)

    input_data.update({
        'prev_date': prev_date,
        'prev_kms': prev_kms,
        'diff_kms': diff_kms,
        'diff_days': diff_days,
        'price_per_l': round(price_per_l, 2),
        'kms_per_l': round(kms_per_l, 2),
        'kms_per_day': round(kms_per_day, 1),
        'cost_per_day': round(cost_per_day, 2),
        'rolling_cost_per_day': round(rolling_cost_per_day, 2),
        'rolling_kms_per_l': round(rolling_kms_per_l, 2),
        'rolling_kms_per_day': round(rolling_kms_per_day, 1),
        'cost': round(cost, 2),
        'amount': round(amount, 2),
    })
    data = format_input_data_to_firebase(input_data)
    return data


def format_input_data_to_firebase(data):
    stg_data = {
        'amount': float(data['amount']),
        'cost_per_day': data['cost_per_day'],
        'diff': data['diff_kms'],
        'diff_days': data['diff_days'],
        'kms_after': data['kms'],
        'kms_before': data['prev_kms'],
        'kms_per_l': data['kms_per_l'],
        'kms_per_day': data['kms_per_day'],
        'last_date': data['prev_date'],
        'place': data['place'],
        'price_per_l': data['price_per_l'],
        'price_total': float(data['cost']),
        'rolling_cost_per_day': data['rolling_cost_per_day'],
        'rolling_kms_per_l': data['rolling_kms_per_l'],
        'rolling_kms_per_day': data['rolling_kms_per_day'],
    }

    final_data = {data['date']: stg_data}
    return final_data


def push_to_db(data, db_name='fuel_raw'):
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
        # Safety measure, if a user calls for a ds (or any partition column)
        try:
            #  and forgets to tick the `is_ds` flag
            return [subset[col] for subset in data.values()]
        except Exception as e:
            print(f"### Failed to use subsets for col={col}\n=========\n{e}\n=========")
            return data.keys()


def delete_rows_within_range(s, e, db_name='fuel_raw'):
    start_date = datetime.combine(s, time(0, 0))
    end_date = datetime.combine(e, time(0, 0))

    # get raw data
    data = get_db_from_firebase(db_name)

    # get all dates
    all_dates = list(get_all_values_from_column('Date', is_ds=True))

    dates_in_range = list(filter(lambda x: start_date <= datetime.strptime(
        x, '%Y-%m-%d') <= end_date, all_dates))

    # Delete each date partition that's in range
    for d in dates_in_range:
        delete_row_by_partition(d, db_name)

    return dates_in_range


def delete_row_by_partition(partition, db_name='fuel_raw'):
    ref = db.reference(f'/{db_name}/{partition}')
    ref.delete()


def get_plots(df, attr_dict):
    ttl = attr_dict['title']
    subplots = attr_dict['subplots']
    num_subplots = len(list(subplots))

    # Generate the plot using Plotly
    plot_layout = go.Layout(title=ttl)

    fig = make_subplots(rows=1, cols=num_subplots)

    annots = []
    for i, sp in enumerate(subplots.keys()):
        fig.add_trace(go.Scatter(x=df['index'], y=df[sp], name=subplots[sp]),
                      row=1, col=i + 1)
        annot = dict(text=subplots[sp], x=(i*1.2 / (num_subplots)) + 0.1, y=1.1,
                     font_size=18, showarrow=False, xref='paper', yref='paper', align='center')
        annots.append(annot)

    # Update layout to display both charts in the same height
    # Add titles to the subplots
    fig.update_layout(title_text=ttl, title_font_size=24,
                      annotations=annots)

    # Render the plot in a template
    plot_div = fig.to_html(full_html=False)
    return plot_div


# predict the next value based on the last value

def predict_next_value(db='fuel_raw'):
    # get last row
    prev_date, prev_row = get_last_row_from_db(db)

    # calc new "kms"
    kms_estimate = float(prev_row['kms_after']) + float((prev_row['diff']))

    # calc new "price_total"
    price_total_estimate = prev_row['price_total']

    # calc new "amount"
    amount_estimate = prev_row['amount']

    # place
    place_estimate = prev_row['place']

    # return all estimates
    return {
        'place': place_estimate, 'amount': round(amount_estimate), 'cost': round(price_total_estimate),
        'kms': round(kms_estimate)
    }
