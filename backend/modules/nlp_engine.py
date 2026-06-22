import re
from typing import List, Dict

class NLPEngine:
    """
    Semantic Storyboarding Engine — Bridges text analysis and video generation.
    Slices long narrative scripts into optimized visual prompts for Wan2.1.
    """
    
    def __init__(self):
        # Keywords for visual style guidance
        self.style_suffix = ", high quality, cinematic lighting, 4k resolution, professional dashboard style"

    def slice_script(self, text: str, target_scenes: int = 6) -> List[str]:
        """
        Segment the script into logical visual blocks using semantic boundary heuristics.
        """
        # Split by sentences (period, exclamation, etc.)
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s for s in sentences if len(s.strip()) > 5]
        
        if not sentences:
            return [text]

        # Calculate how many sentences per scene
        k = max(1, len(sentences) // target_scenes)
        chunks = []
        
        for i in range(0, len(sentences), k):
            chunk = " ".join(sentences[i:i+k])
            chunks.append(chunk)
            
        return chunks[:target_scenes]

    def extract_visual_prompt(self, chunk: str) -> str:
        """
        Identify main entities (nouns) and verbs to construct an optimized prompt.
        """
        # Simple extraction for now (can be expanded with NLTK/SpaCy)
        # We'll focus on creating a descriptive Scene based on the chunk content
        cleaned_text = chunk.replace('"', '').replace("'", "")
        
        # Heuristic: Find mention of data types (charts, metrics, growth)
        prompt_base = "A data visualization scene: "
        
        if any(w in cleaned_text.lower() for w in ["trend", "growth", "rise", "climb"]):
            prompt_base += "A rising line graph with neon blue glowing lines"
        elif any(w in cleaned_text.lower() for w in ["drop", "loss", "decline", "fall"]):
            prompt_base += "A falling bar chart showing negative decline in red colors"
        elif any(w in cleaned_text.lower() for w in ["distribution", "split", "category"]):
            prompt_base += "An animated donut chart breaking down categorical data"
        elif any(w in cleaned_text.lower() for w in ["outlier", "anomaly", "spike"]):
            prompt_base += "A scatter plot with highlighted glowing anomaly points"
        else:
            prompt_base += "An abstract network of data nodes pulsing with information"
            
        return f"{prompt_base}. Context: {cleaned_text[:60]}... {self.style_suffix}"

    def storyboard(self, full_text: str) -> List[Dict[str, str]]:
        """
        Main interface: Converts a full script into a list of {text, visual_prompt}.
        """
        chunks = self.slice_script(full_text)
        scenes = []
        for chunk in chunks:
            scenes.append({
                "text": chunk,
                "visual_prompt": self.extract_visual_prompt(chunk)
            })
        return scenes

# Exposed instance
nlp_engine = NLPEngine()
