import json
import requests
import os
import datetime
from jinja2 import Template

# Loads prediction data from github
def load_data(url):
    """Load JSON data from a URL."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data from {url}")
        return None

# 
def process_data(data, additional_costs_script, raw_today, raw_tomorrow, use_additional_costs):
    """Modify the loaded data and add additional costs and reliability as separate attributes."""
    modified_data = []
    additional_costs_template = Template(additional_costs_script)

    reliability_data = []

    for item in data:
        if isinstance(item, list):
            timestamp = datetime.datetime.fromtimestamp(item[0] / 1000)
            value = item[1]

            # Calculate additional costs based on the current timestamp
            if additional_costs_script:
                additional_costs = float(additional_costs_template.render(now=timestamp))
            else:
                additional_costs = 0.0
            value_with_additional_costs = value + additional_costs

            # Find the corresponding value from raw_today and raw_tomorrow
            today_value = next((item['value'] for item in raw_today if datetime.datetime.fromisoformat(item['start']).strftime('%Y-%m-%d %H:%M:%S') == timestamp.strftime('%Y-%m-%d %H:%M:%S')), None)
            tomorrow_value = next((item['value'] for item in raw_tomorrow if datetime.datetime.fromisoformat(item['start']).strftime('%Y-%m-%d %H:%M:%S') == timestamp.strftime('%Y-%m-%d %H:%M:%S')), None)

            refvalue = 0.0

            if today_value is not None:
                refvalue = today_value

            if tomorrow_value is not None:
                refvalue = tomorrow_value

            # Weather original NordPool sensor contain additional costs
            if use_additional_costs is True:
                compare_value = value_with_additional_costs
            else:
                compare_value = value

            if today_value is not None or tomorrow_value is not None:
                relative_difference = calculate_accuracy(compare_value, refvalue)
            else:
                relative_difference = 0.0

            relative_difference = round(relative_difference, 3)

            modified_data.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'value': round(value, 4),
                'additional_costs': round(additional_costs, 4),
                'value_with_additional_costs': round(value_with_additional_costs, 4)
            })

            if today_value is not None or tomorrow_value is not None:
                reliability_data.append(relative_difference)

    return modified_data, reliability_data

# Calculate value that tries to represent accuracy of predictions from 0 to 1
def calculate_accuracy(value1, value2):
    absolute_difference = abs(value1 - value2)
    sum_absolute_values = abs(value1) + abs(value2)
    relative_difference = absolute_difference / sum_absolute_values
    accuracy = 1 - relative_difference
    accuracy = max(0, min(accuracy, 1))
    
    return accuracy

# Function to calculate the average of the list
def calculate_average(numbers):
    if len(numbers) == 0:
        return 0  # To handle the case where the list is empty
    total_sum = sum(numbers)
    count = len(numbers)
    average = total_sum / count
    return average

# Create/update sensor
def create_sensor(modified_data, reliability_data, token):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    # Calculate the average reliability
    average_reliability = calculate_average(reliability_data)
    
    # Create the sensor
    data = {'state': round(average_reliability, 3), 'attributes': {
        'prediction': modified_data
    }}
    response = requests.post('http://homeassistant:8123/api/states/sensor.nordpool_prediction', headers=headers, json=data)
    if response.status_code == 200:
        print("Sensor created/updated")
    else:
        print("Failed to create sensor.")

# Reads existing Nordpool sensor
def read_sensor(sensor_name, token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'http://homeassistant:8123/api/states/{sensor_name}', headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to read sensor {sensor_name}")
        return None

def main():
    # Here are some variables to edit!!
    # If you have other source for predictions edit this URL. Note format of data.
    url = 'https://raw.githubusercontent.com/vividfog/nordpool-predict-fi/main/deploy/prediction.json'
    # Add your token here
    your_token = 'your_token'
    # Add id of your Nordpool sensor here
    nordpool_senor = 'sensor.nordpool_kwh_fi_eur_3_10_024'
    # Does your Nordpool sensor contain additional costs? True/False
    use_additional_costs = True
    # Add template to calculate additional costs if you want. Note that this handles prices in cents where Nordpool scripts handle in Eurs
    additional_costs_script = ''

    token = os.environ.get('HASS_TOKEN', your_token)

    # Load data
    data = load_data(url)
    if data is None:
        return

    # Read sensor.nordpool_kwh_fi_eur_3_10_024 for raw_today and raw_tomorrow
    sensor_data = read_sensor(nordpool_senor, token)
    if sensor_data is None:
        return

    # Assume raw_today is always available
    raw_today = sensor_data['attributes']['raw_today']

    # Check if tomorrow_valid is true
    if sensor_data['attributes']['tomorrow_valid']:
        raw_tomorrow = sensor_data['attributes']['raw_tomorrow']
    else:
        raw_tomorrow = []

    # Modify data and add additional costs and calculate how reliable prediction was against existing Nordpool prices
    modified_data, reliability_data = process_data(data, additional_costs_script, raw_today, raw_tomorrow, use_additional_costs)

    # Create sensor with modified data
    create_sensor(modified_data, reliability_data, token)

if __name__ == "__main__":
    main()
