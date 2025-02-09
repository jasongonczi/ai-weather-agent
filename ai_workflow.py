import json
import os
import requests
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
weatherapi_api_key = os.getenv("WEATHERAPI_API_KEY")
model = os.getenv("AI_MODEL")

log = []

#I should learn to properly use this at some point
class NoData(Exception):
    pass

#llm response data structure
class WeatherResponseFormat(BaseModel):
    temperature: float = Field(
        description="The current temperature in Fahrenheit or Celsius for the given location."
    )
    response: str = Field(
        description="A natural language response to the user's weather question. Be kind and considerate about the day the user may have due to the weather. Only answer questions about weather."
    )

#Global System Tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the future temperature for a specific location",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "The latitude of a location"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "The longitude of a location"
                    },
                    "days": {
                        "type": "number",
                        "description": "How far to check forecast. Default is 1 day"
                    }
                },
                "required": ["latitude", "longitude", "days"],
                "additionalProperties": False
            },
            "strict": True
        },
    },
]

def setup_prompt(user_input):
    system_prompt = "You are a weather assistant. If no day is specified, assume today. Please provide any available weather alerts to the user. If a region is not specific enough, assume for the user, and give a latitude and longitude. Only answer questions about weather"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    append_debug_log(messages)
    return messages

def weather_response_gate(messages):
    print("Doing weather gate")
    #Ai Response
    completion = client.chat.completions.create(
        model = model,
        messages = messages,
        tools = tools,
    )

    tool_used = getattr(completion.choices[0].message, "tool_calls", None)
    print(completion.model_dump)
    append_debug_log(completion.model_dump)

    #Check if tools were used
    if not tool_used:
        print("No tools used.")
        return

    messages.append(completion.choices[0].message)
    
    return completion

#This might as well return whatever text you want
#I'm just adding this to get varied responses from LLM
def inform_user_ai_usage(messages):
    print("invalid location | informing user")

    system_prompt = "Inform the user that they are only allowed to specify locations. Based on the previous messages, let them know to be more specific only if this is requried. Do not tell them what you will assume"
    ai_usage = {"role": "system", "content": system_prompt}
    messages.append(ai_usage)

    completion = client.chat.completions.create(
        model = model,
        messages = messages,
        tools = tools,
    )

    append_debug_log(completion.choices[0].message)
    return completion.choices[0].message

def get_weather (latitude, longitude, days):
    coordinates = f"{latitude},{longitude}"
    payload = {
        "key": weatherapi_api_key,
        "q": coordinates,
        "days": days,
        #Below are optional
        "aqi": "no",
        "alerts": "yes",
    }

    response = requests.get(
        "http://api.weatherapi.com/v1/forecast.json", params=payload
    )

    data = response.json()
    print(response) #http code
    print(data) #json

    if response.status_code == 200:
        return data
    if response.status_code == 400:
        return {"error": "There is no data for that location."}
    else:
        return {"error": "Could not connect to weather api. Please try again later."}

def call_tool_function(name, args):
    if name == "get_weather":
        return get_weather(**args)
    return {"It seems I can't access my tools right now."}

def use_llm_tool(messages, completion):
    print("using llm tool")
    tool_calls = getattr(completion.choices[0].message, "tool_calls", None)
    print(tool_calls)

    #I shouldn't need this here
    #I also have no clue what the message context would be here
    if not tool_calls:
        return inform_user_ai_usage(message)

    #Only use one tool call if the llm makes multiple for some reason


    for tool_call in tool_calls:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        print(name)
        print(args)

        result = call_tool_function(name, args)

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result)
        })

        append_debug_log(messages)
    return messages

def get_llm_weather_response(messages, response_format):
    print("final response")
    completion = client.beta.chat.completions.parse(
        model = model,
        messages = messages,
        response_format = response_format,
    )

    completion_parsed = completion.choices[0].message.parsed
    
    append_debug_log(completion.choices[0].message)
    return completion_parsed

def append_debug_log(data):
    log.append(str(data) + """___________________________________________________""")
    return log

def clear_debug_log():
    log = []

def start(user_input, debug):
    clear_debug_log()
    if not user_input.strip():
        return "Error: No input provided"
    
    messages = setup_prompt(user_input)

    try:
        llm_completion = weather_response_gate(messages)
        append_debug_log(llm_completion)
    except Exception as e:
        print("Failed to connect to openai. Check availability and rate limit")
        print(f"error: {str(e)}")
        if (debug):
            return f"likely rate limited (~.~) {log}"
        return "likely rate limited (~.~)"
    
    if llm_completion is None:
        final_response = inform_user_ai_usage(messages)
        final_message = getattr(final_response, "content")
        append_debug_log(final_message)
        if (debug):
            return f"{final_message}, {log}"
        return f"{final_message}"
    else:
        mesasges = use_llm_tool(messages, llm_completion)

    try:
        final = get_llm_weather_response(messages, WeatherResponseFormat)
        append_debug_log(final)
    except ValidationError as e:
        print("Failed to format data to WeatherResponseFormat. Attempted to escape format?")
        print("error:" , e.errors())
        append_debug_log(e)
        if (debug):
            return log
        return "Sorry, but I cannot do that for you."
    except NoData as e:
        print("This needs to be handled in get_weather, but is not. Need to parse error code in json")
        append_debug_log(e)
        if (debug):
            return log
        return "There doesn't seem to be any data for that location"
    #Apparently openai can throw a 429 error which causes the entire thing to crash. Not sure if I should catch as a system exit just to have this run no matter what. Don't input twintowers I guess...
    except SystemExit as se:
        append_debug_log(se)
        if (debug):
            return log
        return "Something wen't really wrong and I don\'t know what (╯°□°）╯︵ ┻━┻"
    except Exception as e:
        print("Failed to connect to openai. Check availability and rate limit")
        print(f"error: {str(e)}")
        append_debug_log(e)
        if (debug):
            return log
        return "I'm likely rate limited... I\'m quite useless right now (╥﹏╥)"

    if debug is True:
        result = f"""
                {final.response}
                ___________________________________________________
                Please note the the debug just adds a bunch of stuff from API calls that may be useless or duplicates.
                This feature is really just here for fun, as relevant information will be in console anyways.
                Debug log:
                {log}
                """
        return result
    else:
        return final.response