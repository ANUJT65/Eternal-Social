import io
import re
import json
import logging
import asyncio
import sys
import os
from typing import List

import requests
from bs4 import BeautifulSoup

import torch
import timm
import torch.nn as nn
from torchvision import transforms
import cv2
from PIL import Image

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from web3 import Web3

# ---------------------------
# Global Connection Counter
# ---------------------------
connection_counter = 0

# ---------------------------
# Create FastAPI instance
# ---------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# API Keys & Configuration
# ---------------------------
GOOGLE_API_KEY = "AIzaSyCmkNS6tkGotGtWBEri3Ur0EjQ2fjbAvig"  # Replace with your Gemini API key

# ---------------------------
# Logging Setup
# ---------------------------
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
if not logger.handlers:
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)

# ---------------------------
# Gemini AI Configuration (for text processing)
# ---------------------------
genai.configure(api_key=GOOGLE_API_KEY)
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 4048,
}
safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}
chat_session = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=generation_config,
    safety_settings=safety_settings,
).start_chat(history=[])

# ---------------------------
# Blockchain Setup
# ---------------------------
blockchain_url = "http://127.0.0.1:9545"
web3 = Web3(Web3.HTTPProvider(blockchain_url))
if not web3.is_connected():
    logger.error("Failed to connect to the blockchain!")
    exit(1)
else:
    logger.info("Connected to the blockchain.")

with open("build/contracts/NewsClassification.json", "r") as file:
    contract_json = json.load(file)
contract_abi = contract_json['abi']
deployed_contract_address = "0x4A1c7824240344eE6488E427059700E11bb1776f"  # Replace with your deployed contract address
contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)

# ---------------------------
# Bad Words List
# ---------------------------
BAD_WORDS = ["damn", "shit", "fuck", "bitch", "asshole"]

# ---------------------------
# Reputation Update Function
# ---------------------------
def update_reputation(delta: int, account: str) -> int:
    try:
        checksum_account = Web3.to_checksum_address(account)
        tx_hash = contract.functions.updateReputation(delta).transact({'from': checksum_account})
        web3.eth.wait_for_transaction_receipt(tx_hash)
        new_rep = contract.functions.getReputation(checksum_account).call()
        logger.info(f"Reputation updated by {delta} for account {checksum_account}. New reputation: {new_rep}")
        return new_rep
    except Exception as e:
        logger.error(f"Error updating reputation for account {account}: {e}")
        return None

# ---------------------------
# Xception Model Setup
# ---------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def initialize_xception():
    model = timm.create_model('xception', pretrained=False)
    original_conv1 = model.conv1
    model.conv1 = nn.Conv2d(
        in_channels=1,
        out_channels=original_conv1.out_channels,
        kernel_size=original_conv1.kernel_size,
        stride=original_conv1.stride,
        padding=original_conv1.padding,
        bias=original_conv1.bias is not None
    )
    with torch.no_grad():
        model.conv1.weight = nn.Parameter(original_conv1.weight.sum(dim=1, keepdim=True))
    num_ftrs = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(0.4),
        nn.Linear(num_ftrs, 2)
    )
    return model.to(device)

xception_model = initialize_xception()
xception_model.load_state_dict(torch.load('Models/Model2.pth', map_location=device))
xception_model.eval()

transform = transforms.Compose([
    transforms.Resize((299, 299)),
    transforms.ToTensor(),
    transforms.Normalize([0.5], [0.5])
])

def enhance_edges(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    edges = cv2.Canny(image, 100, 200)
    return edges

def preprocess_edge_image(image_path):
    os.makedirs("temp_processed_images", exist_ok=True)
    edges = enhance_edges(image_path)
    edge_image = Image.fromarray(edges)
    temp_image_path = os.path.join("temp_processed_images", f"edge_{os.path.basename(image_path)}")
    edge_image.save(temp_image_path, format="JPEG")
    return temp_image_path

def predict_with_model(model, image_path, preprocess_fn, switch_labels=False):
    processed_image_path = preprocess_fn(image_path)
    image = Image.open(processed_image_path).convert('L')
    image = transform(image).unsqueeze(0).to(device)
    
    with torch.no_grad():
        outputs = model(image)
        _, predicted = torch.max(outputs, 1)
    
    os.remove(processed_image_path)
    
    if switch_labels:
        predicted = 1 - predicted  # Switch labels if needed
    
    return predicted.item()

class_names = ['Real', 'Fake']

# ---------------------------
# Scraping Functions for AltNews and OpIndia
# ---------------------------
def scrape_altnews(query: str) -> list:
    try:
        url = f"https://www.altnews.in/?s={requests.utils.quote(query)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        for article in soup.find_all('article')[:3]:
            title_elem = article.find('h2', class_='entry-title')
            if title_elem and title_elem.a:
                title = title_elem.a.get_text(strip=True)
                link = title_elem.a.get('href')
                excerpt_elem = article.find('div', class_='entry-content')
                excerpt = excerpt_elem.get_text(strip=True) if excerpt_elem else "No excerpt available"
                articles.append({
                    'title': title,
                    'link': link,
                    'excerpt': excerpt,
                    'source': 'AltNews'
                })
        return articles
    except Exception as e:
        logger.error(f"Error scraping AltNews: {e}")
        return []

def scrape_opindia(query: str) -> list:
    try:
        url = f"https://www.opindia.com/?s={requests.utils.quote(query)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        for article in soup.find_all('article', class_='jeg_post')[:3]:
            title_elem = article.find('h3', class_='jeg_post_title')
            if title_elem and title_elem.a:
                title = title_elem.a.get_text(strip=True)
                link = title_elem.a.get('href')
                excerpt_elem = article.find('div', class_='jeg_post_excerpt')
                excerpt = excerpt_elem.get_text(strip=True) if excerpt_elem else "No excerpt available"
                articles.append({
                    'title': title,
                    'link': link,
                    'excerpt': excerpt,
                    'source': 'OpIndia'
                })
        return articles
    except Exception as e:
        logger.error(f"Error scraping OpIndia: {e}")
        return []

# ---------------------------
# Utility: Check for Reportage Keywords
# ---------------------------
def contains_reportage_keywords(text: str) -> bool:
    keywords = [
        "report", "breaking", "coverage", "incident", 
        "alleged", "sources", "analysis", "update", 
        "news", "confirmed"
    ]
    text_lower = text.lower()
    result = any(kw in text_lower for kw in keywords)
    logger.debug(f"Reportage keyword detection for '{text}': {result}")
    return result

# ---------------------------
# Image Prediction Endpoint
# ---------------------------
@app.post("/predict")
async def predict(file: UploadFile = File(...), ethAddress: str = Form(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        temp_image_path = "temp_image.jpg"
        image.save(temp_image_path)
        
        predicted_class = predict_with_model(xception_model, temp_image_path, preprocess_edge_image, switch_labels=True)
        result = class_names[predicted_class]
        
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        
        logger.info(f"Image prediction result: {result}")
        
        reputation_update = None
        if result.lower() == "fake":
            reputation_update = update_reputation(-50, ethAddress)
        
        return {"result": result, "reputation_update": reputation_update}
    except Exception as e:
        logger.error(f"Error during image prediction: {e}")
        return {"error": "An error occurred during prediction."}

# ---------------------------
# WebSocket Chat Endpoint (for both text and image messages)
# ---------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("A new WebSocket connection has been accepted.")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("A WebSocket connection has been disconnected.")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
        logger.debug(f"Sent personal message: {message}")
    
    async def broadcast(self, message: str, sender: WebSocket):
        for connection in self.active_connections:
            if connection != sender:
                await connection.send_text(message)
        logger.debug(f"Broadcasted message: {message}")

manager = ConnectionManager()

async def process_text(text: str, mode: str) -> str:
    # Don't modify if not in professional mode or if it's a simple greeting
    if mode != "professional" or text.strip().lower() in ["hi", "hello", "hey"]:
        return text
        
    try:
        prompt = f"""
Transform the following message into constructive and empathetic feedback while preserving the core meaning.
Examples of transformations:
- "this app sucks" -> "This application could benefit from some improvements"
- "terrible service" -> "The service quality needs enhancement"
- "worst product ever" -> "This product has significant room for improvement"
- "you're so slow" -> "The response time could be more efficient"
- "this is garbage" -> "This could be enhanced to better meet user expectations"

Guidelines:
- Convert negative criticism into constructive feedback
- Maintain the core issue being raised
- Use professional and respectful language
- Focus on improvement opportunities
- Be specific about what could be better
- Keep the tone balanced and solution-oriented
- DO NOT RESPOND TO PREVIOUS FEEDBACKS...JUST CONVERT THE INPUT TEXT TO A POSITIVE TONE
- DO NOT RESPOND TO INPUTS
- DO NOT USE [] TAGS AND BRACKETS WHILE ADDRESSING, ONLY USE PERSONAL NOUNS YOU , WE, THE etc.
- DO NOT THANK THE USER FOR THE FEEDBACK, JUST CONVERT THE INPUT TEXT TO A POSITIVE TONE

Original message: "{text}"

Respond with ONLY the transformed message, without any explanations."""
        response = await asyncio.to_thread(chat_session.send_message, prompt)
        processed = response.text.strip()
        
        # Take only the first non-empty line
        processed_lines = [line for line in processed.splitlines() if line.strip()]
        if processed_lines:
            processed = processed_lines[0]
            
        logger.debug(f"Original text: '{text}' -> Processed text: '{processed}'")
        return processed
    except Exception as e:
        logger.error(f"Error in process_text: {e}")
        return text

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    global connection_counter
    await manager.connect(websocket)
    connection_counter += 1
    websocket.client_order = connection_counter
    await websocket.send_text(f"YourOrder:{websocket.client_order}")
    logger.info(f"Client #{websocket.client_order} connected via WebSocket.")
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
            except Exception as e:
                logger.error("Error parsing message: " + str(e))
                continue
            
            # Handle image messages directly
            if message_data.get("type") == "image":
                await manager.broadcast(data, websocket)
                await manager.send_personal_message(data, websocket)
                continue
                
            text = message_data.get('text', '')
            mode = message_data.get('mode', '')
            user_account = message_data.get('ethAddress', '')
            
            # ----- Automatic Reportage Analysis Trigger -----
            if contains_reportage_keywords(text):
                news_query = text.strip()
                logger.info(f"Detected news-related text. Using query: {news_query}")
                alt_articles = scrape_altnews(news_query)
                opindia_articles = scrape_opindia(news_query)
                logger.debug(f"AltNews results {alt_articles}")
                logger.debug(f"OpIndia results {opindia_articles}")
                
                if alt_articles:
                    left_summary = f"{alt_articles[0]['title']}\n{alt_articles[0]['excerpt']}\nLink {alt_articles[0]['link']}"
                else:
                    left_summary = "No left wing articles found."
                if opindia_articles:
                    right_summary = f"{opindia_articles[0]['title']}\n{opindia_articles[0]['excerpt']}\nLink {opindia_articles[0]['link']}"
                else:
                    right_summary = "No right wing articles found."
                
                gemini_prompt = f"""
Act as an impartial fact-checker analyzing news coverage.
Below are two sources.

Right Wing Source
{right_summary}

Left Wing Source
{left_summary}

Provide a one-line unbiased analysis that highlights any bias present in these sources.
"""
                logger.debug(f"Gemini prompt\n{gemini_prompt}")
                try:
                    bias_response = await asyncio.to_thread(chat_session.send_message, gemini_prompt)
                    logger.debug(f"Raw Gemini response: {bias_response.text}")
                    bias_analysis_lines = [line for line in bias_response.text.strip().splitlines() if line.strip()]
                    bias_analysis = bias_analysis_lines[0] if bias_analysis_lines else "No bias analysis available."
                except Exception as e:
                    logger.error(f"Error getting bias analysis from Gemini: {e}")
                    bias_analysis = "Error: Gemini analysis not available."
                
                final_output = (
                    f"NEWS-ALERT\nRight Wing Source\n{right_summary}\n\n"
                    f"Left Wing Source\n{left_summary}\n\n"
                    f"Gemini Analysis of Bias\n{bias_analysis}"
                )
                logger.info(f"Final composite news output:\n{final_output}")
                await manager.broadcast(final_output, websocket)
                await manager.send_personal_message(final_output, websocket)
                continue
            # ----- End of News Analysis -----
            
            # Regular Chat Processing
            if text:
                # Show original message to sender
                await manager.send_personal_message(f"You: {text}", websocket)
                
                # Process message if in professional mode
                if mode == "professional":
                    modified_text = await process_text(text, mode)
                    
                    # Show the conversion to the sender
                    if modified_text != text:
                        await manager.send_personal_message(
                            f"System: Your message was made more constructive: '{modified_text}'",
                            websocket
                        )
                    
                    # Send modified version to others
                    await manager.broadcast(f"Client #{websocket.client_order}: {modified_text}", websocket)
                else:
                    # Send original version to others if not in professional mode
                    await manager.broadcast(f"Client #{websocket.client_order}: {text}", websocket)
                
                # Handle reputation adjustments
                rep_adjustment = 0
                if mode == "professional":
                    rep_adjustment += 1
                if "fake" in text.lower():
                    rep_adjustment -= 50
                
                # Check for bad words
                bad_detected = [bad for bad in BAD_WORDS if bad in text.lower()]
                if bad_detected:
                    rep_adjustment -= 5
                    await manager.send_personal_message(
                        f"System: Please note: Some words were flagged as inappropriate.", 
                        websocket
                    )
                
                # Update reputation for non-trivial messages
                if text.strip().lower() not in ["hi", "hello", "hey"] and rep_adjustment != 0 and user_account:
                    new_rep = update_reputation(rep_adjustment, user_account)
                    if new_rep is not None:
                        await manager.send_personal_message(
                            f"System: Reputation updated to: {new_rep}",
                            websocket
                        )
                            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Client #{websocket.client_order} disconnected.")
        await manager.broadcast(f"Client #{websocket.client_order} left the chat", websocket)

@app.post("/register")
async def register(request: Request):
    data = await request.json()
    ethAddress = data.get("ethAddress")
    logger.info(f"Registering Ethereum address: {ethAddress}")
    return {"message": f"Registration successful for address {ethAddress}"}

@app.post("/unregister")
async def unregister(request: Request):
    data = await request.json()
    ethAddress = data.get("ethAddress")
    logger.info(f"Unregistering Ethereum address: {ethAddress}")
    return {"message": f"Unregistration successful for address {ethAddress}"}

@app.get("/profile.png")
async def get_profile():
    return FileResponse("templates/profile.png")

@app.get("/wtf.png")
async def get_wtf():
    return FileResponse("templates/wtf.png")

@app.get("/eternal.png")
async def get_eternal():
    return FileResponse("templates/eternal.png")

@app.get("/")
async def get():
    with open("templates/index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
