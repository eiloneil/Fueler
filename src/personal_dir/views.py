from django.shortcuts import render
from django.http import HttpResponse
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from .forms import TextInputForm, INPUTS
import time
from datetime import datetime
from .fuel_utils import calc_fuel_metrics, get_db_from_firebase

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
    return render(req, 'base.html', {})


def btn_add_row(request):
    print('btn_add_row CLICKED')

    # Get data from the database
    # data = get_db_from_firebase()

    if request.method == 'POST':
        form = TextInputForm(request.POST)
        if form.is_valid():

            input_data = {ip: form.cleaned_data[ip] for ip in INPUTS}
            print('@@@  @@@')
            # Do something with the text_input value, such as store it as a Python variable
            new_data = calc_fuel_metrics(input_data)
            return render(request, 'add_new_row.html', {**input_data})
    else:

        form = TextInputForm(initial=init_text)
    return render(request, 'add_new_row.html', {'form': form})
    print('btn_add_row CLICKED')


def btn_show_raw_data(request):
    print("==== btn_show_raw_data Clicked! ====")

    # Get data from the database
    data = get_db_from_firebase()

    # Pass data as context data to the template
    context = {'data': data}
    print(data)

    # Use the data in your Django view or model as needed
    return render(request, 'raw_data.html', context)
