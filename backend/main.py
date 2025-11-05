from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Website Builder")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class WebsiteRequest(BaseModel):
    prompt: str
    style: str = "modern"

class WebsiteResponse(BaseModel):
    html: str
    css: str
    success: bool
    message: str

@app.get("/")
def root():
    return {"message": "AI Website Builder API", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/generate", response_model=WebsiteResponse)
def generate_website(request: WebsiteRequest):
    import time
    
    # List of models to try in order of preference
    models_to_try = [
        'gemini-2.0-flash-exp',
        'gemini-1.5-flash-latest',
        'gemini-1.5-flash',
        'gemini-1.5-pro-latest',
    ]
    
    system_instruction = """You are an expert web developer specializing in modern, beautiful web design. Generate complete, production-ready HTML and CSS code.
    
    IMPORTANT: Format your response EXACTLY like this (no other text):
    HTML:
    ```html
    <complete html code here>
    ```
    
    CSS:
    ```css
    <complete css code here>
    ```
    
    CRITICAL Requirements:
    
    HTML:
    - Use semantic HTML5 tags (header, nav, main, section, article, footer)
    - DO NOT use external image URLs - use placeholder divs with background colors/gradients instead
    - Use emoji icons (✨🎨📱💼🌟) instead of icon fonts
    - Include proper structure and content hierarchy
    - Use divs with classes for visual elements instead of <img> tags
    
    CSS:
    - Start with a CSS reset (*{margin:0; padding:0; box-sizing:border-box;})
    - Use CSS variables for colors at :root level
    - Create beautiful gradient backgrounds (linear-gradient, radial-gradient)
    - Use flexbox/grid for layouts
    - Add generous padding and margins (at least 2rem-4rem for sections)
    - Use modern font stack: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
    - Font sizes: headings 2rem-4rem, body 1.1rem minimum
    - Line height: 1.6 minimum for readability
    - Add hover effects with transform: translateY(-5px) and box-shadow changes
    - Use border-radius: 12px-20px for cards/buttons
    - Add box-shadow for depth: 0 10px 30px rgba(0,0,0,0.1)
    - Include smooth transitions: transition: all 0.3s ease
    - Make fully responsive with @media queries for mobile (max-width: 768px)
    - Use complementary color schemes (not just black and white)
    - Add background patterns or gradients to sections
    - Style links with colors and hover states
    
    The design should be visually striking, colorful, and immediately impressive."""
    
    style_descriptions = {
        'modern': 'with bold vibrant colors (#667eea to #764ba2 gradients), large typography, card-based layouts, lots of whitespace, glassmorphism effects',
        'minimal': 'with elegant black and white palette, ultra-clean layout, generous negative space, sophisticated typography, accent color (#0066ff)',
        'professional': 'with corporate blue gradients (#4facfe to #00f2fe), structured layout, polished cards, business-appropriate design',
        'creative': 'with bold rainbow gradients (#f093fb to #f5576c), playful animations, asymmetric layouts, artistic flair, vibrant energy'
    }
    
    style_desc = style_descriptions.get(request.style, '')
    user_prompt = f"Create a stunning {request.style} style website {style_desc}: {request.prompt}. Make it visually impressive with rich CSS styling, beautiful colors, and modern design. NO external images - use colored divs and gradients for visual elements."
    
    last_error = None
    response = None
    
    for model_name in models_to_try:
        try:
            print(f"Trying model: {model_name}")
            
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )
            
            response = model.generate_content(
                user_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=8000,
                    temperature=0.7,
                )
            )
            
            # If we get here, the request succeeded
            print(f"✅ Successfully used model: {model_name}")
            break
            
        except Exception as e:
            error_str = str(e)
            print(f"❌ Model {model_name} failed: {error_str}")
            last_error = e
            
            # If it's an overload error or not found, try the next model
            if any(keyword in error_str.lower() for keyword in ["503", "overloaded", "unavailable", "not found", "404"]):
                print(f"Model issue detected, trying next model...")
                time.sleep(0.5)  # Brief pause before trying next model
                continue
            else:
                # For other errors, fail immediately
                raise e
    else:
        # All models failed
        if last_error:
            raise HTTPException(
                status_code=503,
                detail=f"All Gemini models are currently unavailable. Please try again in a few moments. Last error: {str(last_error)}"
            )
    
    if not response:
        raise HTTPException(status_code=500, detail="Failed to generate content")
    
    try:
        
        content = response.text
        print(f"Generated content length: {len(content)}")  # Debug log
        
        # Parse HTML and CSS with better logic
        html = ""
        css = ""
        
        if "HTML:" in content and "CSS:" in content:
            parts = content.split("CSS:")
            html_section = parts[0].replace("HTML:", "").strip()
            css_section = parts[1].strip()
            
            # Extract from code blocks
            if "```html" in html_section:
                html = html_section.split("```html")[1].split("```")[0].strip()
            elif "```" in html_section:
                html = html_section.split("```")[1].split("```")[0].strip()
            else:
                html = html_section
            
            if "```css" in css_section:
                css = css_section.split("```css")[1].split("```")[0].strip()
            elif "```" in css_section:
                css = css_section.split("```")[1].split("```")[0].strip()
            else:
                css = css_section
        else:
            # Fallback: try to extract any HTML/CSS
            if "```html" in content:
                html = content.split("```html")[1].split("```")[0].strip()
            if "```css" in content:
                css = content.split("```css")[1].split("```")[0].strip()
            if not html:
                html = content
        
        print(f"Parsed HTML length: {len(html)}, CSS length: {len(css)}")  # Debug log
        
        return WebsiteResponse(
            html=html,
            css=css,
            success=True,
            message="Website generated successfully"
        )
        
    except Exception as e:
        print(f"Error generating website: {str(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
