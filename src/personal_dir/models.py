from django.db import models

FUEL_RAW_SCHEMA = [
        ('Date', 'date')
        ,('Last Date', 'last_date')
        ,('Place', 'place')
        ,('Amount', 'amount')
        ,('Kms before', 'kms_before')
        ,('Kms After', 'kms_after')
        ,('Diff', 'diff')
        ,('Diff days', 'diff_days')
        ,('Price total', 'price_total')
        ,('Price per L', 'price_per_l')
        ,('Kms per l', 'kms_per_l')
        ,('cost per day', 'cost_per_day')
        ,('Rolling Kms per L', 'rolling_kms_per_l')
        ,('Rolling cost per Day', 'rolling_cost_per_day')
        ]

class FuelRawData(models.Model):
    #TODO Create Fuel_raw as DJ Model

    # Date
    # amount
    # cost_per_day
    # diff
    # diff_days
    # kms_after
    # kms_before
    # kms_per_l
    # last_date
    # place
    # price_per_l
    # price_total
    # rolling_cost_per_day
    # rolling_kms_per_l

    pass

    def __str__(self):
        pass
