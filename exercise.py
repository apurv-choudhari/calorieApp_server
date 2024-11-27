# # import numpy as np
# # from sklearn.cluster import KMeans
# # from sklearn.neighbors import NearestNeighbors
# # from sklearn.preprocessing import LabelEncoder, StandardScaler
# # import pandas as pd
# import warnings
# warnings.filterwarnings("ignore")


# # # Load the dataset
# # data = pd.read_csv("megaGymDataset.csv")  # Replace with your file path

# # data["Rating"] = data["Rating"].fillna(data["Rating"].mean())
# # data['OriginalRating'] = data['Rating']

# # scaler = StandardScaler()
# # data["Rating"] = scaler.fit_transform(data[["Rating"]])

# # # Encode categorical variables
# # label_encoders = {}
# # for col in ["Type", "BodyPart", "Equipment", "Level"]:
# #     le = LabelEncoder()
# #     data[col] = le.fit_transform(data[col])
# #     label_encoders[col] = le

# # # Normalize numerical features
# # scaler = StandardScaler()
# # data["Rating"] = scaler.fit_transform(data[["Rating"]])

# # # Prepare feature set for clustering and recommendations
# # features = data[["Type", "BodyPart", "Equipment", "Level"]]

# # # Cluster exercises using K-Means
# # kmeans = KMeans(n_clusters=3, random_state=42)
# # data["Cluster"] = kmeans.fit_predict(features)

# # # Build a Nearest Neighbors model for content-based recommendations
# # nn_model = NearestNeighbors(n_neighbors=3, metric='euclidean')
# # nn_model.fit(features)

# # # User profile (Example Input)
# # user_input = {
# #     "Type": "Strength",
# #     "BodyPart": "Abdominals",  # Adjust to your dataset values
# #     "Equipment": "Bands",
# #     "Level": "Intermediate",
# #     # "Rating": 4.5,  # Adjust based on normalized value
# # }

# # # Transform user input to match feature space
# # user_vector = [
# #     label_encoders["Type"].transform([user_input["Type"]])[0],
# #     label_encoders["BodyPart"].transform([user_input["BodyPart"]])[0],
# #     label_encoders["Equipment"].transform([user_input["Equipment"]])[0],
# #     label_encoders["Level"].transform([user_input["Level"]])[0],
# #     # scaler.transform([[user_input["Rating"]]])[0][0],
# # ]

# # # Get recommendations
# # distances, indices = nn_model.kneighbors([user_vector])
# # recommended_exercises = data.iloc[indices[0]]

# # # Display recommendations
# # print("Recommended Exercises:")
# # for _, row in recommended_exercises.iterrows():
# #     print(f"- {row['Title']} : {row['Desc']}")

# import pandas as pd
# from sklearn.cluster import KMeans
# from sklearn.neighbors import NearestNeighbors
# from sklearn.preprocessing import LabelEncoder, StandardScaler

# # Load and preprocess dataset
# data = pd.read_csv("megaGymDataset.csv")
# data["Rating"] = data["Rating"].fillna(data["Rating"].mean())
# data['OriginalRating'] = data['Rating']

# scaler = StandardScaler()
# data["Rating"] = scaler.fit_transform(data[["Rating"]])

# label_encoders = {}
# for col in ["BodyPart", "Level"]:
#     le = LabelEncoder()
#     data[col] = le.fit_transform(data[col])
#     label_encoders[col] = le

# features = data[["BodyPart", "Level"]]

# kmeans = KMeans(n_clusters=3, random_state=42)
# data["Cluster"] = kmeans.fit_predict(features)

# nn_model = NearestNeighbors(n_neighbors=3, metric='euclidean')
# nn_model.fit(features)

# # Function to get recommendations


# def get_recommendations(body_part, level):
#     data, label_encoders, nn_model = load_and_process_data()

#     user_vector = [
#         label_encoders["BodyPart"].transform([body_part])[0],
#         label_encoders["Level"].transform([level])[0],
#     ]

#     distances, indices = nn_model.kneighbors([user_vector])
#     recommended_exercises = data.iloc[indices[0]]
#     return recommended_exercises[["Title", "Desc"]].to_dict(orient="records")

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import LabelEncoder, StandardScaler

# Load and preprocess dataset


def load_and_process_data():
    data = pd.read_csv("megaGymDataset.csv")
    data["Rating"] = data["Rating"].fillna(data["Rating"].mean())
    data['OriginalRating'] = data['Rating']

    scaler = StandardScaler()
    data["Rating"] = scaler.fit_transform(data[["Rating"]])

    label_encoders = {}
    for col in ["BodyPart", "Level"]:
        le = LabelEncoder()
        data[col] = le.fit_transform(data[col])
        label_encoders[col] = le

    features = data[["BodyPart", "Level"]]

    kmeans = KMeans(n_clusters=3, random_state=42)
    data["Cluster"] = kmeans.fit_predict(features)

    nn_model = NearestNeighbors(n_neighbors=3, metric='euclidean')
    nn_model.fit(features)

    return data, label_encoders, nn_model


def get_recommendations(body_part, level):
    data, label_encoders, nn_model = load_and_process_data()

    user_vector = [
        label_encoders["BodyPart"].transform([body_part])[0],
        label_encoders["Level"].transform([level])[0],
    ]

    distances, indices = nn_model.kneighbors([user_vector])
    recommended_exercises = data.iloc[indices[0]]
    return recommended_exercises[["Title", "Desc"]].to_dict(orient="records")
