from flask import Flask, request, render_template_string
import ai_workflow
import os
import signal  # Needed for the shutdown() function

app = Flask(__name__)

# Global variables for counting requests.
# (Note: In a multi-worker setup, each worker gets its own copy.)
request_count = 0
max_count = int(os.getenv("MAX_USES", 10))  # Default value in case env var is missing

def shutdown():
    pid = os.getpid()
    os.kill(pid, signal.SIGTERM)

@app.route('/', methods=['GET', 'POST'])
def index():
    global request_count
    result = ''
    uses_left = max_count - request_count - 1

    # If we've reached the last allowed request, respond with a message.
    if request_count == max_count - 1:
        request_count += 1
        return "YOU'VE KILLED ME"

    if request.method == 'POST':
        user_input = request.form.get('input', '').strip()
        debug = "debug_mode" in request.form

        if user_input:
            request_count += 1
            result = ai_workflow.start(user_input, debug)

    return render_template_string('''
        <!doctype html>
        <html>
        <head>
            <title>Weather "App"</title>
        </head>
        <body>
            <h1>Ask about the weather anywhere</h1>
            <form method="post">
                <input type="text" name="input" placeholder="Enter text">
                <br>
                <label for="debug_mode">Enable Debug Mode</label>
                <input type="checkbox" name="debug_mode" id="debug_mode">
                <br>
                <input type="submit" value="Submit">
            </form>
            {% if result %}
                <h2>Result:</h2>
                <p>{{ result }}</p>
                <br>
            {% endif %}
        </body>
        <footer>
            Will self destruct after {{ uses_left }} more uses <br><br><br>
            It's not pretty, but the goal of this project is to practice using python and work with llms.<br>
            If you're curious it works:
            <ol>
                <li>Initial Prompt</li>
                    <ul>
                        <li>Create a generic "you're a weather assistant" system prompt</li>
                        <li>Pass the user input into the user prompt and sent an chat completion request to the LLM</li>
                    </ul>
                <li><a href="https://platform.openai.com/docs/guides/function-calling">Function Calling</a></li>
                    <ul> 
                        <li>There is a single tool available to the LLM called "get_weather"</li>
                        <li>I'm not sure exactly how it decides to use the tool. It colid use just use the function name or also the description.</li>
                        <li>The tool requires: latitude, longitude, and days. These will be passed to WeatherAPI if the tool gets called<li>
                    </ul>
                <ol>
                    <li>If the tool doesn't get called</li>
                        <ul>
                            <li>We create a new system prompt with something like "Inform the user to provide a valid location"</li>
                        </ul>
                    <li>If the tool does get called</li>
                        <ul>
                            <li>We loop over all tool calls and run a get_weather function as many times is required (usually just once)</li>
                        </ul>
                </ol>
                <li>WeatherAPI</li>
                    <ul>
                        <li>Assuming the LLM was able to generate a valid latitude and longitude, we make a request to WeatherAPI and store the received data as a "tool call" message</li>
                        <li>If an invalid location is given, we pass an error as a "tool call" message in json saying "There is no data for that location."</li>
                    </ul>
                <li>Final LLM Response</li>
                    <ul>
                        <li>The final llm response essentially acts as a filter</li>
                        <li>We create a structure for the llm to follow. This consists of "temperature" and a "response." This structure is passed to our chat completion request to openai as a formatted response.</li>
                        <li>With the formatted response, we're pretty much guaranteed to get a response describing the weather of some location while giving it leniency for how it should respond</li>
                        <li>This means you can ask it to respond in the style of trump and even a haiku. However, I think that because I pass every message to maintain context (which is not very necessary), you can still have the llm generate unrelated message</li>
                        <li>A simple solution wolid be to simply create a new message dict with a system prompt, the llm tool call, the tool call data, and have the llm respond to this directly</li>
                        <li>As for responding when no tool call is made, I believe that it can freely maintain context due to the second system prompt we create</li>
                    </ul>
            </ol>
            Code available here: <a href=https://github.com/jasongonczi/ai-weather-agent>https://github.com/jasongonczi/ai-weather-agent</a><br>
            If you like to run this yourself for some reason, you can find the docker image here: <a href=https://hub.docker.com/r/yellowjam/ai-weather-agent>https://hub.docker.com/r/yellowjam/ai-weather-agent</a><br>
            Powered by <a href="https://www.weatherapi.com/" title="Free Weather API">WeatherAPI.com</a>
            <br><br><br>
        </footer>
        </html>
    ''', result=result, uses_left=uses_left)