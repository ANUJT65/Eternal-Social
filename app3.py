import io
import re
import json
import logging
import asyncio
import sys
import os
from typing import List

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
    if mode != "professional":
        return text
    try:
        prompt = f"""
You are a professional language enhancer. Modify the input text to be more professional and courteous without changing its meaning.
Text: '{text}'
Return only the modified text.
"""
        response = await asyncio.to_thread(chat_session.send_message, prompt)
        processed = response.text.strip()
        logger.debug(f"Processed text: '{processed}'")
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
            
            # If message contains a "type" field and it's "image", broadcast it directly.
            if message_data.get("type") == "image":
                # Broadcast the raw JSON string (image message) to all connections
                await manager.broadcast(data, websocket)
                # Optionally, send it back to sender as well:
                await manager.send_personal_message(data, websocket)
            else:
                # Otherwise, assume it's a text message.
                text = message_data.get('text', '')
                mode = message_data.get('mode', '')
                user_account = message_data.get('ethAddress', '')
                logger.info(f"Received text message from client #{websocket.client_order}: '{text}' (Mode: {mode}, Account: {user_account})")
                
                if text:
                    processed_text = await process_text(text, mode)
                    logger.debug(f"Processed text for Client #{websocket.client_order}: {processed_text}")
                    await manager.send_personal_message(f"You: {text}", websocket)
                    await manager.broadcast(f"Client #{websocket.client_order}: {processed_text}", websocket)
                    
                    # Reputation adjustment logic for text messages
                    let_adjustment = 0
                    if mode == "professional":
                        let_adjustment += 1
                    if "fake" in text.lower():
                        let_adjustment -= 50
                    bad_detected = [bad for bad in BAD_WORDS if bad in text.lower()]
                    if bad_detected:
                        let_adjustment -= 5
                        await manager.send_personal_message(f"Bad words detected: {', '.join(bad_detected)}", websocket)
                    if let_adjustment != 0 and user_account:
                        new_rep = update_reputation(let_adjustment, user_account)
                        if new_rep is not None:
                            await manager.send_personal_message(f"Reputation updated: {new_rep}", websocket)
            # End of message processing loop
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
