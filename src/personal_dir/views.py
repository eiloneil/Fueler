from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from .forms import TextInputForm, INPUTS, DateRangeForm
from .models import FUEL_RAW_SCHEMA
import time
from datetime import datetime
from .fuel_utils import (
    calc_fuel_metrics,
    get_db_from_firebase,
    delete_rows_within_range,
    push_to_db,
    FIREBASE_CONNECTION,
    get_plots,
    get_all_values_from_column,
    predict_next_value,
    )
import csv

# import pandas as pd
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
        predict_next_value()
    )


def home_page_view(req):
    print('Initiate Home Page')

    # Get Fuel Raw Data
    data = get_db_from_firebase('/fuel_raw')

    # Create an empty dictionary to hold the flattened table data
    flattened_data = {}

    # Iterate over the sub-dictionaries and flatten the data
    for row in data.values():
        for key, value in row.items():
            if key not in flattened_data:
                flattened_data[key] = []
            flattened_data[key].append(value)

    flattened_data['index'] = list(data.keys())
    df = flattened_data

    # df = pd.DataFrame.from_dict(data, orient='index')

    subplot_attr = {
        "daily": {"title": "Daily Stats",
                  "subplots": {
                      'cost_per_day': 'Price Per Day',
                      'kms_per_l': 'Kms per Liter',
                      'kms_per_day': 'Kms per Day',
                  }
                  },
        "rolling": {"title": "Rolling Stats",
                    "subplots": {
                        'rolling_cost_per_day': 'Rolling Cost/Day',
                        'rolling_kms_per_l': 'Rolling Kms/Liter',
                        'rolling_kms_per_day': 'Rolling Kms/Day',
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
    context = {'data': data, 'fuel_raw_schema':FUEL_RAW_SCHEMA}

    # Use the data in your Django view or model as needed
    return render(request, 'raw_data.html', context)


def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="fuel_raw_{today}.csv"'

    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)

    # Get data from the database
    data = get_db_from_firebase('fuel_raw')

    # Crate Columns names
    writer.writerow([col[0] for col in FUEL_RAW_SCHEMA])

    for ds, row in data.items():
        writer.writerow([ds, *[row.get(col[1]) for col in FUEL_RAW_SCHEMA[1:]]])

    return response

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
        latest_date = max(list(get_all_values_from_column('Date', is_ds=True)))
        form = DateRangeForm(initial={'start_date': latest_date, 'end_date': latest_date})
    context = {
        'form': form,
        **btn_context,

    }
    return render(request, 'remove_dates.html', context)
