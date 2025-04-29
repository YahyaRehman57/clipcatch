from playwright.sync_api import sync_playwright

def fast_fetch_instagram_reel(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            bypass_csp=True,
            viewport={'width': 375, 'height': 667},
            java_script_enabled=True
        )
        page = context.new_page()
        page.goto(url, timeout=15000)

        try:
            video_locator = page.locator("video")
            video_src = video_locator.get_attribute("src")

            browser.close()

            if video_src:
                return video_src
            else:
                return "Error: Could not find video source."
        except Exception as e:
            browser.close()
            return f"Error while fetching video: {str(e)}"



import time
start_time = time.time()

# Call the function
reel_link = "https://www.instagram.com/reel/DIauG4VKFKs/?igsh=MTNnNWZ3Z2pnaml5bw=="
real_video_link = fast_fetch_instagram_reel(reel_link)
print("Download Link:", real_video_link)

# Calculate the time taken
end_time = time.time()
execution_time = end_time - start_time
print(f"Execution Time: {execution_time} seconds")