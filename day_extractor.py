from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import csv
import os
import json


class Holiday:
    def __init__(self, title, description, category):
        self.title = title
        self.description = description
        self.category = category

    def __dict__(self):
        return {
            "title": self.title,
            "description": self.description,
            "category": self.category
        }


def init_webdriver():
    # Initialize and return a WebDriver instance
    # Example with Firefox; replace with your browser of choice
    driver = webdriver.Firefox()
    return driver


def scrape_day_holidays(driver, day_url, include_monthly_holidays=False):
    driver.get(day_url)
    holidays = []

    # Wait for the dynamic content to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.single-holiday.w-dyn-item')))

    # Scrape daily holidays
    holiday_elements = driver.find_elements(By.CSS_SELECTOR, '.single-holiday.w-dyn-item')
    for holiday_div in holiday_elements:
        title = holiday_div.find_element(By.CSS_SELECTOR, 'h3').text.strip()
        description = holiday_div.find_element(By.CSS_SELECTOR, 'div.pd-left-and-right-20px').text.strip()
        category = holiday_div.find_element(By.CSS_SELECTOR, 'div.badge-primary').text.strip()
        holidays.append(Holiday(title, description, category))

    # Conditionally scrape monthly holidays
    if include_monthly_holidays:
        monthly_holiday_elements = driver.find_elements(By.CSS_SELECTOR, '.month-block .single-holiday.w-dyn-item')
        for holiday_div in monthly_holiday_elements:
            title = holiday_div.find_element(By.CSS_SELECTOR, 'h3').text.strip()
            description = holiday_div.find_element(By.CSS_SELECTOR, 'div.pd-left-and-right-20px').text.strip()
            category = "Monthly"
            holidays.append(Holiday(title, description, category))

    return holidays


def decide_and_append_to_csv(holidays):
    with open('./days.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for holiday in holidays:
            print(f"\nTitle: {holiday.title}\nDescription: {holiday.description}\nCategory: {holiday.category}\n")
            decision = input("Include this holiday? (y/n): ")
            # decision = 'y'
            if decision.lower() == 'y':
                writer.writerow([holiday.title])


def write_holidays_to_json(holidays, filename):
    # Read existing data
    try:
        with open(filename, 'r') as f:
            existing_holidays = json.load(f)
    except Exception as e:
        print(f"Error reading existing holidays: {e}")
        existing_holidays = []

    # Convert existing holidays to set for faster lookup
    existing_holidays_set = set(tuple(holiday.items()) for holiday in existing_holidays)

    # Filter out holidays that already exist and add new ones
    new_holidays = []
    for holiday in holidays[:]:
        holiday_dict = holiday.__dict__()
        if tuple(holiday_dict.items()) in existing_holidays_set:
            holidays.remove(holiday)
        else:
            new_holidays.append(holiday_dict)

    # Append new holidays to existing ones
    existing_holidays.extend(new_holidays)

    # Write data back to file
    with open(filename, 'w') as f:
        json.dump(existing_holidays, f)

    return holidays


def drive_scraping_future_holidays(driver):
    start_date = datetime.now() + timedelta(days=7)
    end_date = start_date + timedelta(days=7)
    current_date = start_date
    last_processed_month = None

    while current_date <= end_date:
        # Manually format the date to ensure compatibility across platforms
        month = current_date.strftime("%B").lower()
        day = current_date.strftime("%d")
        # Remove leading zero from day if present
        day = day.lstrip('0')
        formatted_date = f"{month}-{day}"

        day_url = f"https://www.holidaycalendar.io/day/{formatted_date}-holidays"
        print(f"Scraping holidays for: {formatted_date}")

        include_monthly_holidays = current_date.day == 1 or current_date.month != last_processed_month
        holidays = scrape_day_holidays(driver, day_url, include_monthly_holidays=include_monthly_holidays)

        # write holiday objects to json history file
        write_holidays_to_json(holidays, 'holiday_history.json')

        if include_monthly_holidays:
            last_processed_month = current_date.month

        decide_and_append_to_csv(holidays)
        current_date += timedelta(days=1)


if __name__ == "__main__":
    driver = init_webdriver()
    try:
        drive_scraping_future_holidays(driver)
    finally:
        driver.quit()
