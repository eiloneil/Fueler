from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from .forms import TextInputForm, INPUTS, DateRangeForm
import time
from datetime import datetime
from .fuel_utils import (calc_fuel_metrics, get_db_from_firebase, delete_rows_within_range, push_to_db, FIREBASE_CONNECTION, get_plots)
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from django.shortcuts import render


TEST = True
# TEST = False

# Today's date
today = datetime.today().strftime('%Y-%m-%d')
init_text = {'date': today}
if TEST:
    init_text.update(
        {
            'place': 'יילו ירושלים', 'amount': '31.5', 'cost': '280.44', 'kms': '58500',
        }
    )


def home_page_view(req):
    print('Initiate Home Page')

    # Get Fuel Raw Data
    data = get_db_from_firebase('/fuel_raw')
    df = pd.DataFrame.from_dict(data, orient='index')

    # daily_plot_div = get_daily_plots(df)
    # rolling_plot_div = get_rolling_plots(df)

    subplot_attr = {
        "daily": {"title": "Daily Stats",
                  "subplots": {
                      'cost_per_day': 'Price Per Day',
                      'kms_per_l': 'Kms per Liter',
                  }
                  },
        "rolling": {"title": "Rolling Stats",
                    "subplots": {
                        'rolling_cost_per_day': 'Rolling Cost/Day',
                        'rolling_kms_per_l': 'Rolling Kms/Liter',
                    }
                    }
    }
    plot_divs = {ttl: get_plots(df, attr_dict) for ttl, attr_dict in subplot_attr.items()}

    return render(req, 'base.html', {'plot_div': plot_divs})



def btn_add_row(request):
    print('btn_add_row CLICKED')

    btn_context = {'btn_txt': "Submit", 'switch_action': {
        'btn_name': 'Delete previous data', 'url': 'delete_row'}}
    if request.method == 'POST':
        form = TextInputForm(request.POST)
        if form.is_valid():

            input_data = {ip: form.cleaned_data[ip] for ip in INPUTS}
            # Do something with the text_input value, such as store it as a Python variable
            new_data = calc_fuel_metrics(input_data, request)
            if new_data is None:
                pass
            else:
                push_to_db(new_data, 'fuel_raw')
                btn_context.update(
                    {'is_submitted_successfully': input_data['date']})
    else:

        form = TextInputForm(initial=init_text)

    return render(request, 'add_new_row.html', {'form': form, **btn_context, })


def btn_show_raw_data(request):
    print("==== btn_show_raw_data Clicked! ====")

    # Get data from the database
    data = get_db_from_firebase()

    # Pass data as context data to the template
    context = {'data': data}

    # Use the data in your Django view or model as needed
    return render(request, 'raw_data.html', context)


def btn_delete_row(request):

    btn_context = {'btn_txt': "Delete",
                   'switch_action': {'btn_name': 'Add another row', 'url': 'add_row'}, }
    if request.method == 'POST':
        form = DateRangeForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            deleted_dates = delete_rows_within_range(
                start_date, end_date, db_name='fuel_raw')
            num_deleted_dates = len(deleted_dates)
            if num_deleted_dates > 0:
                messages.error(
                    request, f'Successfully Deleted {num_deleted_dates} date{"s" if num_deleted_dates>1 else ""}: {", ".join(deleted_dates)}')
            else:
                messages.error(request, 'No Dates were Deleted')

    else:
        form = DateRangeForm(initial={'start_date': today, 'end_date': today})
    context = {
        'form': form,
        **btn_context,

    }
    return render(request, 'remove_dates.html', context)
