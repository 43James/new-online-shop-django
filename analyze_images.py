import os
import google.generativeai as genai
import sys

def main():
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    img1_path = r"C:\Users\IT\.gemini\antigravity\brain\4d0bbf42-123b-43b9-8b84-e7af3091cf33\.user_uploaded\media__1785986311068.png"
    img2_path = r"C:\Users\IT\.gemini\antigravity\brain\4d0bbf42-123b-43b9-8b84-e7af3091cf33\.user_uploaded\media__1785986704594.png"
    
    for path in [img1_path, img2_path]:
        if os.path.exists(path):
            print(f"Analyzing {path}...")
            img = genai.upload_file(path)
            response = model.generate_content([img, "Describe this UI design in detail, including layout, colors, elements, and text."])
            print(response.text)
            print("-" * 50)
            
if __name__ == "__main__":
    main()
