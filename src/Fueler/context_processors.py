
def button_list(request):
    buttons = [
        {'text': 'Home', 'url': '/'},
        {'text': 'View All', 'url': '/fuel/view'},
        {'text': 'Add/Delete', 'url': '/add_row'},
    ]
    return {'buttons': buttons}
