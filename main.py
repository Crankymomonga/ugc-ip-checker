# === 1. Preprocessor ===
def classify_content_type(file_path):
    if file_path.endswith(('.jpg', '.png', '.jpeg')):
        return 'image'
    elif file_path.endswith(('.mp4', '.mov')):
        return 'video'
    elif file_path.endswith(('.mp3', '.wav')):
        return 'audio'
    elif file_path.endswith(('.txt', '.docx')):
        return 'text'
    else:
        return 'unknown'


# === 2. ImageHandler ===
from google.cloud import vision

def detect_logos_google(image_path):
    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.logo_detection(image=image)
    return [logo.description for logo in response.logo_annotations]

from ultralytics import YOLO

def detect_custom_logo_yolo(image_path):
    model = YOLO("custom-logo-detection.pt")
    results = model(image_path)
    return results.pandas().xyxy[0].to_dict(orient='records')


# === 3. AudioHandler ===
import requests

def match_audio_audd(file_path, api_token):
    files = {'file': open(file_path, 'rb')}
    data = {'api_token': api_token, 'return': 'apple_music,spotify'}
    response = requests.post('https://api.audd.io/', data=data, files=files)
    return response.json()


# === 4. TextHandler ===
def check_plagiarism_copyleaks(text, api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {"base64": text.encode("utf-8").decode("utf-8")}
    response = requests.post("https://api.copyleaks.com/v3/education/submit/file", headers=headers, json=data)
    return response.json()


# === 5. VideoHandler ===
import cv2
import os

def extract_frames(video_path, output_folder, frame_rate=1):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    vidcap = cv2.VideoCapture(video_path)
    fps = int(vidcap.get(cv2.CAP_PROP_FPS))
    count = 0
    success, image = vidcap.read()
    while success:
        if count % (fps * frame_rate) == 0:
            cv2.imwrite(os.path.join(output_folder, f"frame{count}.jpg"), image)
        success, image = vidcap.read()
        count += 1
    return os.listdir(output_folder)


# === 6. RiskScorer ===
def score_risk(detections):
    score = 0
    for detection in detections:
        score += 10  # Dummy logic: each hit = +10 risk
    return min(score, 100)


# === 7. Notification (Slack Webhook) ===
def notify_slack(webhook_url, message):
    payload = {"text": message}
    response = requests.post(webhook_url, json=payload)
    return response.status_code == 200


# === 8. FastAPI Routing ===
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_path = f"temp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    content_type = classify_content_type(file_path)
    result = {"file": file.filename, "type": content_type}

    if content_type == 'image':
        result["google"] = detect_logos_google(file_path)
        result["yolo"] = detect_custom_logo_yolo(file_path)
    elif content_type == 'audio':
        result["audio_match"] = match_audio_audd(file_path, "YOUR_AUDD_API_TOKEN")
    elif content_type == 'text':
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        result["plagiarism"] = check_plagiarism_copyleaks(text, "YOUR_COPYLEAKS_API_KEY")
    elif content_type == 'video':
        frames = extract_frames(file_path, "frames")
        result["frames"] = frames

    risk = score_risk(result.get("google", []) + result.get("yolo", []))
    result["risk_score"] = risk

    notify_slack("YOUR_SLACK_WEBHOOK_URL", f"[ALERT] UGC submission risk: {risk} - File: {file.filename}")
    return JSONResponse(content=result)


# === 9. Embedding-based IP Similarity (using OpenAI) ===
import openai

def get_embedding(text, api_key):
    openai.api_key = api_key
    response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
    return response['data'][0]['embedding']


def cosine_similarity(vec1, vec2):
    import numpy as np
    vec1, vec2 = np.array(vec1), np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def check_similarity_to_known(text, known_ip_texts, api_key):
    user_emb = get_embedding(text, api_key)
    similarities = []
    for known_text in known_ip_texts:
        known_emb = get_embedding(known_text, api_key)
        sim = cosine_similarity(user_emb, known_emb)
        similarities.append((known_text, sim))
    return sorted(similarities, key=lambda x: -x[1])
