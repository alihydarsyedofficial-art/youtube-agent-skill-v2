import os
import json
import random
from PIL import Image, ImageDraw, ImageFont

def generate_video_and_assets():
    os.makedirs("videos/queue", exist_ok=True)
    
    # Simple dynamic topic selection for kids/story content
    topics = [
        {"title": "The Lost Puppy's Night Adventure", "niche": "pet_stories", "topic_id": "pet_001"},
        {"title": "Tiny Star's Big Journey", "niche": "bedtime_stories", "topic_id": "bed_001"},
        {"title": "The Magic Color Forest", "niche": "learning_colors", "topic_id": "col_001"},
        {"title": "Brave Little Duckling Rescue", "niche": "animal_rescue", "topic_id": "ani_001"}
    ]
    
    selected = random.choice(topics)
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
    d.text((100, 300), selected["title"], fill=(255, 255, 0))
    img.save(thumb_path)
    
    # 3. Create Sidecar JSON metadata matching main.py requirements
    metadata = {
        "title": f"{selected['title']} | Bedtime Stories for Kids",
        "description": "Enjoy this amazing animated story designed specially for kids and toddlers. Don't forget to subscribe for more little wonders!",
        "tags": ["bedtime stories", "kids animation", "cartoon for kids", selected["niche"]],
        "category_id": "24", # Entertainment
        "topic_id": selected["topic_id"],
        "made_for_kids": True,
        "chapters": [
            {"title": "Start", "time": "00:00"},
            {"title": "The Adventure Begins", "time": "00:15"},
            {"title": "Happy Ending", "time": "00:45"}
        ]
    }
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"Successfully generated queue assets for: {selected['title']}")

if __name__ == "__main__":
    generate_video_and_assets()
