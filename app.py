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
            Will self destruct after {{ uses_left }} more uses <br>
            It's not pretty, but the goal of this project is to practice using python and work with llms.<br>
            If you're curious it works:
            <ol>
                <li>We setup a generic "you're a weather assistant" system prompt and pass the user input as the user's prompt to give the llm something to respond to</li>
                <li>We create a tool for the llm to use (if it decides to use it). The tool, if called, is seen inside of the llm's message reply</li>
                <li>If the tool doesn't get called, we create a new system prompt saying something like 'tell the user to ask for the weather of a location'</li>
                <li>If the tool does get used, an api request is made to WeatherAPI</li>
                <li>Assuming there is a valid location, we send this data to the llm and ask it to reply in a specific format. Formatted responses are only available for gpt-4o models and newer</li>
            </ol>
            If you like to run this yourself for some reason, you can find the docker image here: https://hub.docker.com/r/yellowjam/ai-weather-agent <br>
            Powered by <a href="https://www.weatherapi.com/" title="Free Weather API">WeatherAPI.com</a>
            <br><br><br>
        </footer>
        </html>
    ''', result=result, uses_left=uses_left)