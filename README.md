A demo ai agent that fetches weather information from WeatherAPI; can display it in any format/style you request or simply give you the information. Currently requires a payed or trial version of the API (as the llm can request forcast of future days). To remove this, just modify the tool under {#Global system tools} comment and the get_weather function.

Environment values required are specified in .env-template

You can build the image locally or pull from yellowjam/ai-weather-agent on docker hub