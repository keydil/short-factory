"""
Fetches a visual for each script segment:
1. Try Pexels stock video first (free API, already has motion, usually the best match).
2. Fall back to a Leonardo AI generated image (spends your Leonardo credits) which
   gets an animated Ken Burns pan/zoom in the assembler so it doesn't look static.

Veo is intentionally NOT called here. Google's Veo video generation through your
Google AI Pro subscription only works inside the Gemini app / Flow website (manual
clicks). The programmatic Veo API bills separately per-second with no free tier, so
it's left out of this free pipeline on purpose. If you want a Veo shot in a video,
generate it manually in Flow, drop the file in assets/manual_veo/, and reference
it directly instead of calling fetch_visual_for_segment() for that segment.
"""
import os
import time
import requests
import config

PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"
LEONARDO_GENERATE_URL = "https://cloud.leonardo.ai/api/rest/v1/generations"


def fetch_pexels_clip(query: str, output_path: str, min_duration: int = 3) -> bool:
    headers = {"Authorization": config.PEXELS_API_KEY}
    params = {"query": query, "orientation": "portrait", "per_page": 5}

    resp = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=20)
    if resp.status_code != 200:
        return False

    for video in resp.json().get("videos", []):
        if video.get("duration", 0) < min_duration:
            continue
        files = sorted(video["video_files"], key=lambda f: f.get("width", 0))
        candidates = [f for f in files if f.get("width", 0) >= 720]
        chosen = candidates[0] if candidates else files[-1]

        video_data = requests.get(chosen["link"], timeout=30).content
        with open(output_path, "wb") as f:
            f.write(video_data)
        return True

    return False


def fetch_leonardo_image(prompt: str, output_path: str, poll_interval: int = 3, timeout: int = 90) -> bool:
    headers = {
        "Authorization": f"Bearer {config.LEONARDO_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"prompt": prompt, "width": 1024, "height": 1792, "num_images": 1}

    resp = requests.post(LEONARDO_GENERATE_URL, headers=headers, json=payload, timeout=30)
    if resp.status_code not in (200, 201):
        print(f"  Leonardo request failed: {resp.status_code} {resp.text[:200]}")
        return False

    generation_id = resp.json()["sdGenerationJob"]["generationId"]

    elapsed = 0
    while elapsed < timeout:
        time.sleep(poll_interval)
        elapsed += poll_interval
        status_resp = requests.get(f"{LEONARDO_GENERATE_URL}/{generation_id}", headers=headers, timeout=20)
        data = status_resp.json().get("generations_by_pk", {})
        if data.get("status") == "COMPLETE":
            image_url = data["generated_images"][0]["url"]
            with open(output_path, "wb") as f:
                f.write(requests.get(image_url, timeout=30).content)
            return True
        if data.get("status") == "FAILED":
            return False

    return False


def fetch_visual_for_segment(keywords: list, output_dir: str, segment_index: int) -> dict:
    """Returns {"path": str, "type": "video" | "image"}"""
    os.makedirs(output_dir, exist_ok=True)

    for kw in keywords:
        video_path = os.path.join(output_dir, f"segment_{segment_index}.mp4")
        if fetch_pexels_clip(kw, video_path):
            return {"path": video_path, "type": "video"}

    image_path = os.path.join(output_dir, f"segment_{segment_index}.jpg")
    prompt = ", ".join(keywords) + ", cinematic, high detail, vertical composition"
    if fetch_leonardo_image(prompt, image_path):
        return {"path": image_path, "type": "image"}

    raise RuntimeError(f"Could not fetch any visual for segment {segment_index} (keywords: {keywords})")
