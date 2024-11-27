# from flask import Flask, render_template, request, jsonify
# from exercise import get_recommendations  # Import the function

# app = Flask(__name__)


# @app.route("/")
# def index():
#     body_parts = ['Abdominals', 'Adductors', 'Abductors', 'Biceps', 'Calves',
#                   'Chest', 'Forearms', 'Glutes', 'Hamstrings', 'Lats', 'Lower Back',
#                   'Middle Back', 'Traps', 'Neck', 'Quadriceps', 'Shoulders',
#                   'Triceps']  # Example body parts
#     levels = ['Beginner', 'Intermediate', 'Expert']  # Example levels
#     return render_template("exercise.html", body_parts=body_parts, levels=levels)


# @app.route("/recommend", methods=["POST"])
# def recommend():
#     # Get data from the form
#     body_part = request.form.get("body_part")
#     level = request.form.get("level")

#     if not body_part or not level:
#         return jsonify({"error": "Missing form data"}), 400

#     # Call the recommendation function
#     recommendations = get_recommendations(body_part, level)

#     return jsonify(recommendations)  # Return the recommendations as JSON


# if __name__ == "__main__":
#     app.run(debug=True)

from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Home route


@app.route("/", methods=["GET", "POST"])
def index():
    exercises = []  # To store exercises
    error_message = None

    if request.method == "POST":
        # Get user input
        muscle = request.form.get("muscle").lower()
        difficulty = request.form.get("difficulty").lower()

        # API call
        api_url = f"https://api.api-ninjas.com/v1/exercises?muscle={muscle}&difficulty={difficulty}"
        headers = {'X-Api-Key': 'ThMgHV6VS4iYBAsvrUnNRg==vDzibI5DsOwhxevU'}
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            exercises = response.json()[:5]  # Get only 5 exercises
            if not exercises:
                error_message = f"No exercises found for {muscle} at {difficulty} level."
        else:
            error_message = f"Error {response.status_code}: Unable to fetch exercises."

    return render_template("exercise.html", exercises=exercises, error_message=error_message)


if __name__ == "__main__":
    app.run(debug=True)
