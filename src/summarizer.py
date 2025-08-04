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
        # Token limits for different models
        self.token_limits = {
            "gpt-4-turbo-preview": 128000,  # Total context window
            "gpt-3.5-turbo": 16385,
        }
        self.max_chunk_tokens = 10000  # Safe chunk size for processing
    
    def summarize_transcript(self, 
                           transcript: str, 
                           style: str = "detailed",
                           max_length: Optional[int] = None) -> Dict:
        if not transcript:
            raise ValueError("No transcript provided for summarization")
        
        # Estimate token count (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = len(transcript) // 4
        
        prompts = self._get_prompts(style)
        
        # Check if we need to chunk the transcript
        if estimated_tokens > self.max_chunk_tokens:
            print(f"\n📊 Large transcript detected (~{estimated_tokens:,} tokens)")
            print("   Splitting into chunks for processing...")
            return self._summarize_chunked_transcript(transcript, style, prompts)
        
        if style == "detailed":
            return self._detailed_summary(transcript, prompts, max_length)
        else:
            return self._simple_summary(transcript, prompts, max_length)
    
    def _split_transcript_into_chunks(self, transcript: str, max_chunk_chars: int = 40000) -> List[str]:
        """Split transcript into chunks at sentence boundaries"""
        sentences = re.split(r'(?<=[.!?])\s+', transcript)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            if current_length + sentence_length > max_chunk_chars and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _summarize_chunked_transcript(self, transcript: str, style: str, prompts: Dict) -> Dict:
        """Summarize a long transcript by chunking it"""
        chunks = self._split_transcript_into_chunks(transcript)
        chunk_summaries = []
        
        print(f"   Processing {len(chunks)} chunks...")
        
        # Summarize each chunk
        for i, chunk in enumerate(chunks):
            print(f"   Summarizing chunk {i+1}/{len(chunks)}...")
            try:
                if style == "detailed":
                    # For detailed summaries, use brief style for chunks
                    chunk_prompts = self._get_prompts("brief")
                    chunk_summary = self._simple_summary(chunk, chunk_prompts, 500)
                else:
                    chunk_summary = self._simple_summary(chunk, prompts, 300)
                
                chunk_summaries.append(chunk_summary["summary"])
            except Exception as e:
                print(f"   ⚠️  Warning: Failed to summarize chunk {i+1}: {e}")
                # Try with smaller model
                try:
                    chunk_summary = self._simple_summary_with_fallback(chunk, prompts, 300)
                    chunk_summaries.append(chunk_summary["summary"])
                except:
                    chunk_summaries.append(f"[Chunk {i+1} summary failed]")
        
        # Create final summary from chunk summaries
        combined_summary = "\n\n".join(chunk_summaries)
        
        print("   Creating final summary from chunks...")
        final_prompt = {
            "system": "You are an expert at synthesizing information. Create a cohesive summary from these section summaries.",
            "user": f"Create a {style} summary by combining these section summaries into a cohesive whole:\n\n{combined_summary}"
        }
        
        try:
            if style == "detailed":
                return self._detailed_summary(combined_summary, final_prompt, 2000)
            else:
                return self._simple_summary(combined_summary, final_prompt, 1000)
        except Exception as e:
            # Fallback: return concatenated summaries
            print(f"   ⚠️  Warning: Failed to create final summary: {e}")
            return {
                "summary": combined_summary,
                "style": style,
                "word_count": len(combined_summary.split()),
                "sections": {"main": combined_summary},
                "note": "This is a concatenation of chunk summaries due to length constraints."
            }
    
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

This is a transcript of a video, so when referring to the source material, speak of it as a video rather than a transcript.

Transcript:
{transcript}"""
            },
            "bullet": {
                "system": "You are a summarizer who creates clear bullet-point summaries.",
                "user": "Create a bullet-point summary of the main ideas in this transcript:\n\n{transcript}"
            }
        }
        
        return prompts.get(style, prompts["detailed"])
    
    def _simple_summary_with_fallback(self, transcript: str, prompts: Dict, max_length: Optional[int]) -> Dict:
        """Try to summarize with gpt-3.5-turbo as fallback"""
        try:
            messages = [
                {"role": "system", "content": prompts["system"]},
                {"role": "user", "content": prompts["user"].format(transcript=transcript)}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=max_length or 1000,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content
            
            return {
                "summary": summary,
                "style": "simple",
                "word_count": len(summary.split()),
                "sections": {"main": summary},
                "model": "gpt-3.5-turbo"
            }
            
        except Exception as e:
            raise Exception(f"Fallback summarization also failed: {str(e)}")
    
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
            error_str = str(e)
            if "maximum context length" in error_str or "token" in error_str.lower():
                print(f"   ⚠️  Token limit exceeded, trying with gpt-3.5-turbo...")
                return self._simple_summary_with_fallback(transcript, prompts, max_length)
            raise Exception(f"Summarization failed: {error_str}")
    
    def _detailed_summary(self, transcript: str, prompts: Dict, max_length: Optional[int] = 2000) -> Dict:
        try:
            messages = [
                {"role": "system", "content": prompts["system"]},
                {"role": "user", "content": prompts["user"].format(transcript=transcript)}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                max_tokens=max_length,
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
            error_str = str(e)
            if "maximum context length" in error_str or "token" in error_str.lower():
                print(f"   ⚠️  Token limit exceeded, trying with gpt-3.5-turbo...")
                return self._simple_summary_with_fallback(transcript, prompts, max_length)
            raise Exception(f"Summarization failed: {error_str}")
    
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
