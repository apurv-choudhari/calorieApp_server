import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

# Load CSV data
meal_data = pd.read_csv('food_data/meal_plan_data.csv')


def preprocess_data():
    """
    Preprocesses the meal data for model training.
    
    Adds a 'goal' column to classify each meal based on its calorie value:
    - 'Weight Loss' if calories <= 300
    - 'Muscle Gain' if calories >= 400
    - 'Maintenance' otherwise
    
    Normalizes the selected features (calories, protein, carbs, fat) 
    using StandardScaler.
    
    Returns:
        tuple: A tuple (scaled_features, goals) where:
            - scaled_features (ndarray): Normalized feature values.
            - goals (Series): Corresponding goals for each meal.
    """
    # Convert the 'calories' column to numeric, coercing errors to NaN
    meal_data['calories'] = pd.to_numeric(meal_data['calories'],
                                          errors='coerce')

    # Drop rows with NaN values in 'calories'
    meal_data.dropna(subset=['calories'], inplace=True)

    # Adding a 'goal' column based on calorie values
    meal_data['goal'] = meal_data['calories'].apply(
        lambda x: 'Weight Loss'
        if x <= 300 else ('Muscle Gain' if x >= 400 else 'Maintenance'))

    # Selecting relevant features for model training
    features = meal_data[['calories', 'protein', 'carbs', 'fat']]

    # Standardizing features to have a mean of 0 and a variance of 1
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    return scaled_features, meal_data['goal']


def train_model():
    """
    Initializes and trains a K-Nearest Neighbors (KNN) classifier model 
    using the preprocessed meal data.
    
    The model uses 5 neighbors to classify meals into categories based on the 
    preprocessed calorie, protein, carbs, and fat values.
    
    Returns:
        KNeighborsClassifier: The trained KNN model.
    """
    # Preprocess data for training
    X, y = preprocess_data()

    # Initialize KNN classifier with 5 neighbors
    knn_model = KNeighborsClassifier(n_neighbors=5)

    # Train the KNN model
    knn_model.fit(X, y)

    return knn_model


# Train the model once
model = train_model()


def recommend_meal_plan(goal, calories, protein, carbs, fat):
    """
    Recommends meals from the dataset that match the user's dietary goal 
    and macro-nutrient preferences.

    Uses the trained KNN model to classify the user's input data into a 
    dietary goal (Weight Loss, Muscle Gain, or Maintenance) and then 
    filters meals from the dataset based on the predicted goal.

    Args:
        goal (str): The user's dietary goal, used here only for reference.
        calories (int): The user's target calories.
        protein (int): The user's target protein intake in grams.
        carbs (int): The user's target carbohydrate intake in grams.
        fat (int): The user's target fat intake in grams.

    Returns:
        list: A list of dictionaries, where each dictionary represents a meal 
              that matches the predicted dietary goal.
    """
    # Initialize StandardScaler and fit-transform user input data
    scaler = StandardScaler()
    input_data = scaler.fit_transform([[calories, protein, carbs, fat]])

    # Predict the dietary goal using the trained KNN model
    prediction = model.predict(input_data)

    # Filter meals based on the predicted goal
    recommended_meals = meal_data[meal_data['goal'] == prediction[0]].to_dict(
        orient='records')

    return recommended_meals
