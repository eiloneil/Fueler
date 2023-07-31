from django import forms

INPUTS = [
    'date',
    'place',
    'amount',
    'cost',
    'kms',
]

class TextInputForm(forms.Form):
    text_boxes = {}
    for i in INPUTS:
        kwargs = {'label': i, 'max_length': 100, 'widget': forms.TextInput(
            attrs={'placeholder': i, 'class': 'text-input'})}

        text_boxes[i] = forms.CharField(**kwargs)

    date, place, amount, cost, kms = text_boxes.values()




class DateRangeForm(forms.Form):
    start_date = forms.DateField(label='Start Date')
    end_date = forms.DateField(label='End Date')
