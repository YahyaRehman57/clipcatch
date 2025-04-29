from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.sync_api import sync_playwright  # Use sync API
import time
import uvicorn

# Create the FastAPI app
app = FastAPI()

# Function to fetch Instagram video URL using sync Playwright API
def fast_fetch_instagram_reel(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            bypass_csp=True,
            viewport={'width': 375, 'height': 667},
            java_script_enabled=True
        )
        page = context.new_page()
        page.goto(url, timeout=5000)

        # Block unnecessary resources to speed up page loading
        page.route("**/*.{png,jpg,jpeg,gif,css,woff,woff2}", lambda route: route.abort())

        try:
            video_locator = page.locator("video")
            video_src = video_locator.get_attribute("src")

            browser.close()

            if video_src:
                return video_src
            else:
                raise HTTPException(status_code=404, detail="Video source not found.")
        except Exception as e:
            browser.close()
            raise HTTPException(status_code=500, detail=f"Error while fetching video: {str(e)}")

# API route to fetch Instagram reel video URL
@app.post("/fetch_instagram_reel/")
def fetch_instagram_reel():
    start_time = time.time()

    # Fetch the video URL from the Instagram reel using the URL from the request (or default)
    try:
        url_to_use = "https://www.instagram.com/reel/DIauG4VKFKs/?igsh=MTNnNWZ3Z2pnaml5bw=="
        video_url = fast_fetch_instagram_reel(url_to_use)  # Call the sync function directly
        end_time = time.time()
        execution_time = end_time - start_time
        return {
            "video_url": video_url,
            "execution_time": execution_time
        }
    except HTTPException as e:
        raise e

# Automatically start the server when the script is run
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
