# Nordpool-Prediction-Sensor
Script that fetches Nordpool prediction from vividfogs nordpool-predict-fi project

# What this does?
When run this reads data from "https://raw.githubusercontent.com/vividfog/nordpool-predict-fi/main/deploy/prediction.json". 
This data is processed and stored in sensor "sensor.nordpool_prediction" attribute Prediction. 
Reads also offical Nordpool price from sensor in your Home Assistant instance. 
This is used to compare how close prediction was compared to published price. 
Sensor state will be number from 0 to 1 and tries to represent how good accuracy was. 1 means prediction was accurate. This is mostly for personal curiosity. 

You can also provide template to include additional costs similar to what Nordpool sensor allows. 

# Installation
Copy loadprediction.py script to /config/custom_components/

At end of file there are few variables to configure.

your_token:

You need to get token from your Home Assistant instance. You can get it by clicking your user name on left bar. Go to Security tab and Log-lived access tokens.

nordpool_sensor:

Name of nordpool sensor in your Home Assistance instance.

use_additional_costs:

Does your nordpool sensor that you are using as a comparison use additional costs.

additional_costs_script:

Here enter your script for additional costs if you want to.

In configuration.yaml add
~~~
shell_command:
  update_nordpool_prediction: "python3 /config/custom_components/loadprediction.py"
~~~
Create automation that calls service "shell_command.update_nordpool_prediction"

As source data updates few times a day it doesnt make sense to run this more than once or twice a day.

*Optional*

If you prefer not to have sensor with compaint
~~~
This entity ('sensor.nordpool_prediction') does not have a unique ID, therefore its settings cannot be managed from the UI.
~~~
Create template sensor with same name before running script in UI or YAML.
