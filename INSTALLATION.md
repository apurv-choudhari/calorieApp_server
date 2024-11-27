
# Installation Guide for METAFIT

This guide provides step-by-step instructions for installing and setting up METAFIT on your local machine, using Docker, or deploying it on Kubernetes.

---

## Table of Contents
- [System Requirements](#system-requirements)
- [MongoDB Installation](#mongodb-installation)
- [Repository Setup](#repository-setup)
- [Setting up Environment](#setting-up-environment)
- [Running METAFIT Locally](#running-metafit-locally)
- [Running METAFIT on Docker](#running-metafit-on-docker)
- [Deploying on Kubernetes](#deploying-on-kubernetes)

---

## System Requirements

- **Python**: Ensure you have Python 3.8 or later installed on your system.
- **MongoDB**: Required for database operations.
- **Docker**: (optional) Required if you want to run the application using Docker.
- **Kubernetes**: (optional) Required if you plan to deploy the app on a Kubernetes cluster.

---

## MongoDB Installation

1. Install MongoDB using the following link: [MongoDB Installation Guide](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows)

2. Start the MongoDB server. Make sure it's accessible at `localhost:27017` (default configuration).

---

## Repository Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/RAV-Organization/SE_Project3_calorieApp_server.git
   ```

   Or download the repository as a `.zip` file and extract it to your local machine:
   
   [GitHub Download Link](https://github.com/RAV-Organization/SE_Project3_calorieApp_server/archive/refs/heads/meta_2.0_final.zip)

2. **Navigate to the Project Directory**

   ```bash
   cd calorieApp_server
   ```

---

## Setting up Environment

1. **Install the required packages** by running the following command in the terminal:

   ```bash
   pip install -r requirements.txt
   ```

2. **Install OpenAI SDK** (version 0.28.0)

   ```bash
   pip install openai==0.28.0
   ```

3. **Configure OpenAI API Key**:

   - Go to [OpenAI Platform](https://platform.openai.com/) and create an API key.
   - Open `application.py` and add your API key to the line:

     ```python
     openai.api_key = 'YOUR_API_KEY'
     ```

4. **Insert Food Data** (First-time setup)

   Run the script below to populate initial data for the food selection field in the application:

   ```bash
   python insert_food_data.py
   ```

---

## Running METAFIT Locally

To start the application locally:

1. **Run the Application**

   ```bash
   python application.py
   ```

2. **Access the Application**

   Open your browser and go to:

   - [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## Running METAFIT on Docker

If you prefer using Docker:

1. **Build and Start Docker Containers**

   ```bash
   docker-compose up -d --build
   ```

2. **Access the Application**

   Open your browser and go to:

   - [http://127.0.0.1:5000/](http://127.0.0.1:5000/) or [http://localhost:5000/](http://localhost:5000/)

---

## Deploying on Kubernetes

To deploy METAFIT on Kubernetes:

1. **Apply Deployment and Service YAML files**

   ```bash
   kubectl apply -f app-deployment.yaml
   kubectl apply -f app-service.yaml
   ```

2. **Access the Application**

   - Retrieve the external IP (for LoadBalancer) or Cluster IP for the service:

     ```bash
     kubectl get service flask-mongo-service
     ```

3. **Open in Browser**

   Use the IP address or hostname provided by Kubernetes to access the application.
