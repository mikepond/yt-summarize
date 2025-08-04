import os
import re
from typing import Optional, Dict, List
from openai import OpenAI


class Summarizer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def summarize_transcript(self, 
                           transcript: str, 
                           style: str = "detailed",
                           max_length: Optional[int] = None) -> Dict:
        if not transcript:
            raise ValueError("No transcript provided for summarization")
        
        prompts = self._get_prompts(style)
        
        if style == "detailed":
            return self._detailed_summary(transcript, prompts)
        else:
            return self._simple_summary(transcript, prompts, max_length)
    
    def _get_prompts(self, style: str) -> Dict[str, str]:
        prompts = {
            "brief": {
                "system": "You are a concise summarizer. Create brief, clear summaries.",
                "user": "Summarize this transcript in 2-3 paragraphs, focusing on the key points:\n\n{transcript}"
            },
            "detailed": {
                "system": "You are an expert summarizer. Create comprehensive, well-structured summaries.",
                "user": """Create a detailed summary of this transcript with:
1. A brief overview (1-2 paragraphs)
2. Key points and main ideas (bullet points)
3. Important details or examples mentioned
4. Conclusion or takeaways

Transcript:
{transcript}"""
            },
            "bullet": {
                "system": "You are a summarizer who creates clear bullet-point summaries.",
                "user": "Create a bullet-point summary of the main ideas in this transcript:\n\n{transcript}"
            }
        }
        
        return prompts.get(style, prompts["detailed"])
    
    def _simple_summary(self, transcript: str, prompts: Dict, max_length: Optional[int]) -> Dict:
        try:
            messages = [
                {"role": "system", "content": prompts["system"]},
                {"role": "user", "content": prompts["user"].format(transcript=transcript)}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                max_tokens=max_length or 1000,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content
            
            return {
                "summary": summary,
                "style": "simple",
                "word_count": len(summary.split()),
                "sections": {"main": summary}
            }
            
        except Exception as e:
            raise Exception(f"Summarization failed: {str(e)}")
    
    def _detailed_summary(self, transcript: str, prompts: Dict) -> Dict:
        try:
            messages = [
                {"role": "system", "content": prompts["system"]},
                {"role": "user", "content": prompts["user"].format(transcript=transcript)}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content
            sections = self._parse_sections(summary)
            
            return {
                "summary": summary,
                "style": "detailed",
                "word_count": len(summary.split()),
                "sections": sections
            }
            
        except Exception as e:
            raise Exception(f"Summarization failed: {str(e)}")
    
    def _parse_sections(self, summary: str) -> Dict[str, str]:
        sections = {}
        current_section = "overview"
        current_content = []
        
        lines = summary.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            if any(keyword in line.lower() for keyword in ['overview', 'introduction']):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "overview"
                current_content = []
            elif any(keyword in line.lower() for keyword in ['key points', 'main ideas', 'main points']):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "key_points"
                current_content = []
            elif any(keyword in line.lower() for keyword in ['details', 'examples']):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "details"
                current_content = []
            elif any(keyword in line.lower() for keyword in ['conclusion', 'takeaway', 'summary']):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "conclusion"
                current_content = []
            else:
                current_content.append(line)
        
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def create_chapter_summary(self, transcript_with_timestamps: str) -> List[Dict]:
        try:
            prompt = """Analyze this timestamped transcript and identify logical chapters or sections.
For each chapter, provide:
1. Start timestamp
2. Chapter title
3. Brief description (1-2 sentences)

Format as:
[HH:MM:SS] Chapter Title
Description of what is covered in this section.

Transcript:
{transcript}"""
            
            messages = [
                {"role": "system", "content": "You are an expert at identifying logical sections in video transcripts."},
                {"role": "user", "content": prompt.format(transcript=transcript_with_timestamps)}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            chapters_text = response.choices[0].message.content
            return self._parse_chapters(chapters_text)
            
        except Exception as e:
            print(f"Warning: Could not create chapter summary: {e}")
            return []
    
    def _parse_chapters(self, chapters_text: str) -> List[Dict]:
        chapters = []
        lines = chapters_text.split('\n')
        
        current_chapter = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            timestamp_match = re.match(r'\[(\d{1,2}:\d{2}:\d{2})\](.+)', line)
            if timestamp_match:
                if current_chapter:
                    chapters.append(current_chapter)
                
                current_chapter = {
                    "timestamp": timestamp_match.group(1),
                    "title": timestamp_match.group(2).strip(),
                    "description": ""
                }
            elif current_chapter:
                current_chapter["description"] += line + " "
        
        if current_chapter:
            chapters.append(current_chapter)
        
        return chapters