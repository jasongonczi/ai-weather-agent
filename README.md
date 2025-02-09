A demo ai agent (workflow) that fetches weather information from WeatherAPI; can display it in any format/style you request or simply give you the information.
Currently requires a payed or trial version of the API (as the llm can request forcast of future days). To remove this, just modify the tool under {#Global system tools} comment and the get_weather function.
This workflow only supports the gpt-4o or gpt-4o-mini models

Environment values required are specified as:

    OPENAI_API_KEY = (your openai api key)
    WEATHERAPI_API_KEY = (your weatherapi api key)
    MAX_USES = (max uses before blocking normal access to input) #page is very much vulnerable to replay attacks or manually forming a POST
    AI_MODEL = (openai model; either gpt-4o or gpt-4o-mini)

You can build the image locally or pull from yellowjam/ai-weather-agent on docker hub

A single comment on the replay attack: You can quickly test this by setting the max uses to 2, running the model once, opening a new tab to the server to check if "YOU'VE KILLED ME" is showing, and refreshing the previous tab to have it generate a new resposne.
You can probably manually form an http request to still generate any weather response you want.