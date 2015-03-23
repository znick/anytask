import datetime

from years.models import Year
    
def get_current_year():
    today = datetime.date.today()
    year = today.year
    if today.month < 9:
        year -= 1

    try:
        return Year.objects.get(start_year=year)
    except Year.DoesNotExist:
        return None

def get_or_create_current_year():
    today = datetime.date.today()
    year = today.year
    if today.month < 9:
        year -= 1
       
    return Year.objects.get_or_create(start_year=year)[0]
