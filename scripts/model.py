import google.generativeai as genai


genai.configure(api_key="AIzaSyBFfBsJ_usL_gEEGlOS2foLl39rbZSdjkY")




class GeminiService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('models/gemini-1.5-flash')


    def get_response(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error: {str(e)}"



# Example usage:
if __name__ == "__main__":
    API_KEY = "AIzaSyBFfBsJ_usL_gEEGlOS2foLl39rbZSdjkY"  # Replace with your Gemini API key
    gemini = GeminiService(API_KEY)
    
    prompt = "Explain quantum computing in simple terms."
    result = gemini.get_response(prompt)
    print("Response from Gemini:\n", result)

