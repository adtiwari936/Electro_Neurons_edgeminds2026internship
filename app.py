# Import Flask, which is the main class used to create a web application object.
# render_template is used to return HTML files from the templates folder.
# request is used to read incoming client data such as JSON or form input.
# jsonify converts Python dictionaries into proper JSON HTTP responses.
from flask import Flask, render_template, request, jsonify

# Import the custom function that performs the main agent task.
# This function is expected to accept a topic and return a result in string, dictionary, or list form.
from agent import run_agent

# Import Python's built-in JSON module.
# It is used to convert Python objects like dictionaries and lists into JSON-formatted text.
import json

# Create the Flask application instance.
# This object is the central part of the Flask app and stores routes, settings, and behavior.
app = Flask(__name__)

# Disable browser caching for static files.
# This is useful during development because updated CSS, JS, or images will load immediately.
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# Define the homepage route.
# The / route is the first page opened when the application is accessed.
# methods=["GET", "POST"] means this route can respond to both GET and POST requests.
@app.route("/", methods=["GET", "POST"])
def index():
    # Return the index.html template from the templates directory.
    # render_template sends HTML content back to the browser as the response.
    return render_template("index.html")

# Define a health-check endpoint.
# Such an endpoint is commonly used to verify whether the backend server is active and working.
@app.route("/health", methods=["GET"])
def health():
    # Return a JSON response indicating that the server is running properly.
    # jsonify automatically formats the dictionary into valid JSON.
    return jsonify({
        "status": "ok",
        "message": "Autonomous Local Research Agent backend is running."
    })

# Define the main API endpoint that runs the agent.
# This route accepts POST requests because it receives input data from the client.
@app.route("/run", methods=["POST"])
def run():
    try:
        # Read JSON data from the request body.
        # silent=True prevents Flask from throwing an error if the request does not contain valid JSON.
        # If nothing is received, {} is used as a safe default.
        data = request.get_json(silent=True) or {}

        # Extract the topic from the JSON object.
        # If topic is missing, use an empty string and remove extra spaces using strip().
        topic = (data.get("topic") or "").strip()

        # Validate the topic.
        # If the user did not provide a topic, return an error response with HTTP status 400.
        if not topic:
            return jsonify({
                "topic": "",
                "report": "",
                "raw": None,
                "error": "Topic is required."
            }), 400

        # Run the agent using the provided topic.
        # The function may return different data types depending on implementation.
        result = run_agent(topic)

        # If the returned result is a dictionary, try to extract the most useful report field.
        # Different agent implementations may use different keys such as report, final_report, answer, or answers.
        if isinstance(result, dict):
            candidate = (
                result.get("report")
                or result.get("final_report")
                or result.get("answer")
                or result.get("answers")
            )

            # If the extracted value is a dictionary, convert it into formatted JSON text.
            # indent=2 makes the output readable.
            # ensure_ascii=False keeps Unicode characters unchanged.
            if isinstance(candidate, dict):
                report_text = json.dumps(candidate, indent=2, ensure_ascii=False)

            # If the extracted value is a list, convert it into formatted JSON text.
            elif isinstance(candidate, list):
                report_text = json.dumps(candidate, indent=2, ensure_ascii=False)

            # If the extracted value is a normal value like string, number, or boolean, convert it to string.
            elif candidate is not None:
                report_text = str(candidate)

            # If no suitable field is found, convert the full result dictionary into JSON text.
            else:
                report_text = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            # If the result is not a dictionary, directly convert it to string.
            report_text = str(result)

        # Return the final successful response as JSON.
        # It includes the submitted topic, formatted report, raw agent output, and error as None.
        return jsonify({
            "topic": topic,
            "report": report_text,
            "raw": result,
            "error": None
        }), 200

    # Handle any unexpected exception during execution.
    # This prevents the application from crashing and sends a proper error response.
    except Exception as e:
        return jsonify({
            "topic": "",
            "report": "",
            "raw": None,
            "error": f"{type(e).__name__}: {str(e)}"
        }), 500

# This condition checks whether the file is being run directly.
# It prevents the server from starting automatically if this file is imported as a module.
if __name__ == "__main__":
    # Start the Flask development server.
    # host="0.0.0.0" makes the server accessible from all network interfaces.
    # port=5001 sets the port number.
    # debug=True enables auto-reload and detailed error pages during development.
    app.run(host="0.0.0.0", port=5001, debug=True)