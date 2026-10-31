import os
import json
import random
from PIL import Image, ImageDraw, ImageFont
from google import genai

def generate_video_and_assets():
    os.makedirs("videos/queue", exist_ok=True)
    
    # Initialize Gemini Client using environment variable
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing!")
        
    client = genai.Client(api_key=api_key)
    
    # Prompt Gemini to generate creative content ideas
    prompt = (
        "Generate a creative and viral YouTube Shorts title and a short description "
        "for a kids' bedtime or pet story video. "
        "Provide the output strictly in JSON format with keys: 'title', 'niche', 'topic_id', 'description', and a list of 'tags'."
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        # Clean up response text if wrapped in markdown code blocks
        clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        selected = json.loads(clean_text)
    except Exception as e:
        print(f"Gemini API generation failed, falling back to default topic: {e}")
        selected = {
            "title": "The Magic Starry Night Adventure",
            "niche": "bedtime_stories",
            "topic_id": "bed_002",
            "description": "Enjoy this amazing animated bedtime story designed specially for kids and toddlers.",
            "tags": ["bedtime stories", "kids animation", "cartoon for kids", "bedtime_stories"]
        }
    
    base_name = f"video_{random.randint(1000, 9999)}"
    
    video_path = f"videos/queue/{base_name}.mp4"
    thumb_path = f"videos/queue/{base_name}_thumb.jpg"
    json_path = f"videos/queue/{base_name}.json"
    
    # 1. Create a dummy blank video file using touch/write for structure simulation
    with open(video_path, "wb") as f:
        f.write(b"\x00" * 1024) # Placeholder bytes for media container
        
    # 2. Create thumbnail image using Pillow
    img = Image.new('RGB', (1280, 720), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    
    # Draw text safely on thumbnail (handling long titles)
    title_text = selected.get("title", "Kids Story")
    d.text((80, 300), title_text[:40], fill=(255, 255, 0))
    img.save(thumb_path)
    
    # 3. Create Sidecar JSON metadata matching main.py requirements
    metadata = {
        "title": f"{selected.get('title')} | Kids Stories",
        "description": selected.get("description", "Enjoy this amazing animated story."),
        "tags": selected.get("tags", ["kids stories", "animation"]),
        "category_id": "24", # Entertainment
        "topic_id": selected.get("topic_id", "gen_001"),
        "made_for_kids": True,
        "chapters": [
            {"title": "Start", "time": "00:00"},
            {"title": "The Journey", "time": "00:15"},
            {"title": "Happy Ending", "time": "00:45"}
        ]
    }
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"Successfully generated queue assets via Gemini for: {selected.get('title')}")

if __name__ == "__main__":
    generate_video_and_assets()
