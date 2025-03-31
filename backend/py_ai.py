
"""

import google.generativeai as ai
import requests
from bs4 import BeautifulSoup
import time
import urllib.parse

# Configure the Gemini API
ai.configure(api_key=API_KEY)
model = ai.GenerativeModel("gemini-pro")
chat = model.start_chat()

def get_city_coordinates(city):
    #Fetch city latitude and longitude using Open-Meteo API (Free & No API Key).
    open_meteo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1"

    try:
        response = requests.get(open_meteo_url, timeout=None)
        response.raise_for_status()
        data = response.json()

        if "results" in data and len(data["results"]) > 0:
            return data["results"][0]["latitude"], data["results"][0]["longitude"]
        else:
            return None, None

    except requests.exceptions.RequestException:
        return None, None

def get_nearby_hospitals(city):
    #Finds hospitals near the given city using OpenStreetMap Overpass API.
    print("\nFetching top hospitals near you...")

    lat, lon = get_city_coordinates(city)
    if lat is None or lon is None:
        return "❌ Could not determine city coordinates. Try a larger city or check the spelling."

    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f#
    [out:json];
    node["amenity"="hospital"](around:10000,{lat},{lon});
    out body;
    #

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.post(overpass_url, data={"data": query}, headers=headers, timeout=None)
        response.raise_for_status()

        hospitals = response.json().get("elements", [])[:10]  # Get top 10 hospitals
        if not hospitals:
            return "❌ No hospitals found within 10 km. Try searching a nearby city."

        hospital_info = []
        for i, hospital in enumerate(hospitals):
            name = hospital.get("tags", {}).get("name", f"Hospital {i+1}")
            lat, lon = hospital["lat"], hospital["lon"]
            maps_url = f"https://www.google.com/maps/search/?q={lat},{lon}"

            hospital_info.append(f"🏥 **{name}**\n📍 Location: {city}\n🔗 [Google Maps Link]({maps_url})\n")

        return "\n".join(hospital_info)

    except requests.exceptions.RequestException as e:
        return f"❌ Error fetching hospital data: {e}"

# Web scraping for doctor details
def get_specialized_doctor(disease):
    print(f"\nSearching for dermatologists specializing in {disease}...")

    search_url = "https://www.justdial.com/India/dermatologists"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=25)  # Added headers
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find doctor details (adjust selectors based on actual site structure)
        doctors = soup.find_all("div", class_="jcn")
        doctor_info = []

        # Collect top 3 doctors (you can scrape more if necessary)
        for doctor in doctors[:3]:
            name = doctor.find("a").get_text() if doctor.find("a") else "Not Available"
            contact = doctor.find("span", class_="contact-info").get_text() if doctor.find("span", class_="contact-info") else "Not Available"
            address = doctor.find("span", class_="address").get_text() if doctor.find("span", class_="address") else "Not Available"

            doctor_info.append(f"👨‍⚕️ **{name}**\n"
                               f"🔹 Specialization: Dermatologist\n"
                               f"📍 {address}\n"
                               f"📞 {contact}\n")

        if not doctor_info:
            return "❌ Could not find any doctors for this disease. Try again later."

        return "\n".join(doctor_info)

    except requests.exceptions.RequestException as e:
        return f"❌ Error fetching doctor data: {e}"

def py_ai_main(confirmed_disease, severity):
# # Start chatbot
# print("Chatbot: Hello! I can help you with skin disease information. Let's begin.")

# while True:
    # Ask user for details
    # disease = input("Chatbot: What is the name of the skin disease? ").strip()
    # severity = input("Chatbot: How severe is it (mild, moderate, severe)? ").strip()
    location = input("\nWhere are you located (City, State, Country)? ").strip()

    # Get response from AI model
    response = chat.send_message(
        f"Provide detailed information about {confirmed_disease}. Include:\n"
        "- External and internal symptoms (in bullet points)\n"
        "- Steps to take care of it\n"
    )

    # Get hospital and doctor details
    hospital_info = get_nearby_hospitals(location)
    # doctor_info = get_specialized_doctor(confirmed_disease)

    # Display results
    print("\nHere is the information you need:\n")
    print(f"- **Disease**: {confirmed_disease}")
    print(f"- **Severity**: {severity}")
    print(f"- **Location**: {location}\n")
    print(f"**Symptoms & Care Instructions:**\n{response.text}\n")
    print(f"**Nearby Hospitals:**\n{hospital_info}\n")
    # print(f"**Specialized Doctors:**\n{doctor_info}\n")

    # # Ask if the user wants to continue
    # again = input("Chatbot: Do you want to check another disease? (yes/no): ").strip().lower()
    # if again != "yes":
    #     print("Chatbot: Take care! Goodbye!")
    #     break
"""
# API Key

import google.generativeai as ai
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import urllib.parse

# Load .env file
load_dotenv()

API_KEY = os.getenv("API_KEY")

# Configure the Gemini API
ai.configure(api_key=API_KEY)
# model = ai.GenerativeModel("gemini-pro")
model = ai.GenerativeModel("gemini-1.5-flash")
chat = model.start_chat()

def get_city_coordinates(city):
    """Fetch city latitude and longitude using Open-Meteo API (Free & No API Key)."""
    open_meteo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1"

    try:
        response = requests.get(open_meteo_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "results" in data and len(data["results"]) > 0:
            return data["results"][0]["latitude"], data["results"][0]["longitude"]
        else:
            return None, None

    except requests.exceptions.RequestException:
        return None, None

def get_nearby_hospitals(city):
    """Finds hospitals near the given city using OpenStreetMap Overpass API."""
    lat, lon = get_city_coordinates(city)
    if lat is None or lon is None:
        return ["❌ Could not determine city coordinates. Try a larger city or check the spelling."]

    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    node["amenity"="hospital"](around:10000,{lat},{lon});
    out body;
    """
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.post(overpass_url, data={"data": query}, headers=headers, timeout=10)
        response.raise_for_status()

        hospitals = response.json().get("elements", [])[:5]  # Get top 5 hospitals
        if not hospitals:
            return ["❌ No hospitals found within 10 km. Try searching a nearby city."]

        hospital_info = []
        for i, hospital in enumerate(hospitals):
            name = hospital.get("tags", {}).get("name", f"Hospital {i+1}")
            # print("1111")
            lat, lon = hospital["lat"], hospital["lon"]
            # print("2222")
            maps_url = f"https://www.google.com/maps/search/?q={lat},{lon}"
            # print("3333")
            hospital_info.append({"name": name, "location": city, "maps_url": maps_url})
            # print("4444")

        return hospital_info

    except requests.exceptions.RequestException:
        return ["❌ Error fetching hospital data."]

def py_ai_main(confirmed_disease, severity, location):
    """Processes the disease, severity, and user location, then returns results."""
    response = chat.send_message(
        f"Provide detailed information about the skin disease name present in the title {confirmed_disease} ingnoring the title itself. Include:\n"
        "- External and internal symptoms (in bullet points)\n"
        "- Steps to take care of it\n"
    )

    # Get hospital details
    hospital_info = get_nearby_hospitals(location)
    
    print(f"**Symptoms & Care Instructions:**\n{response.text}\n")

    # Return results as a dictionary for the frontend
    return {
        "disease": confirmed_disease,
        "severity": severity,
        "location": location,
        "symptoms_care": response.text,
        "hospitals": hospital_info,
    }
