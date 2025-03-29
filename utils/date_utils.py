from datetime import datetime, timedelta
import pandas as pd
import calendar

def get_month_start_end(year, month):
    """
    Get the start and end dates for a given month
    
    Args:
        year (int): Year
        month (int): Month (1-12)
    
    Returns:
        tuple: (start_date, end_date) as datetime objects
    """
    start_date = datetime(year, month, 1)
    
    # Get the last day of the month
    _, last_day = calendar.monthrange(year, month)
    end_date = datetime(year, month, last_day)
    
    return start_date, end_date

def get_quarter_start_end(year, quarter):
    """
    Get the start and end dates for a given quarter
    
    Args:
        year (int): Year
        quarter (int): Quarter (1-4)
    
    Returns:
        tuple: (start_date, end_date) as datetime objects
    """
    if quarter == 1:
        return datetime(year, 1, 1), datetime(year, 3, 31)
    elif quarter == 2:
        return datetime(year, 4, 1), datetime(year, 6, 30)
    elif quarter == 3:
        return datetime(year, 7, 1), datetime(year, 9, 30)
    elif quarter == 4:
        return datetime(year, 10, 1), datetime(year, 12, 31)
    else:
        raise ValueError("Quarter must be 1, 2, 3, or 4")

def get_year_start_end(year):
    """
    Get the start and end dates for a given year
    
    Args:
        year (int): Year
    
    Returns:
        tuple: (start_date, end_date) as datetime objects
    """
    return datetime(year, 1, 1), datetime(year, 12, 31)

def get_date_range_periods(start_date, end_date, freq='M'):
    """
    Generate a list of periods between start and end dates
    
    Args:
        start_date (datetime): Start date
        end_date (datetime): End date
        freq (str): Frequency ('M' for month, 'Q' for quarter, 'Y' for year)
    
    Returns:
        list: List of period strings
    """
    dates = pd.date_range(start=start_date, end=end_date, freq=freq)
    
    if freq == 'M':
        return [date.strftime("%Y-%m") for date in dates]
    elif freq == 'Q':
        return [f"{date.year}-Q{date.quarter}" for date in dates]
    elif freq == 'Y':
        return [str(date.year) for date in dates]
    else:
        return [date.strftime("%Y-%m-%d") for date in dates]

def get_month_name(month_num):
    """
    Get the month name from its number
    
    Args:
        month_num (int): Month number (1-12)
    
    Returns:
        str: Month name
    """
    return calendar.month_name[month_num]

def get_current_year_month():
    """
    Get current year and month
    
    Returns:
        tuple: (year, month) as integers
    """
    now = datetime.now()
    return now.year, now.month
