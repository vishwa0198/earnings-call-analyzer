# utils/topic_extractor.py
import os
import openai
from typing import List, Dict, Any
import json

def get_openai_client():
    """Get OpenAI client instance."""
    return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_topics_from_section(section_text: str, section_type: str, company_name: str) -> List[Dict[str, str]]:
    """
    Extract 3-5 key business-relevant topics from a section using AI.
    """
    client = get_openai_client()
    
    # Create section-specific prompts
    if section_type == "opening_remarks":
        prompt = create_opening_remarks_prompt(section_text, company_name)
    else:  # Q&A section
        prompt = create_qa_prompt(section_text, company_name)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a financial analyst expert at extracting key business topics from earnings call transcripts. Focus on specific, actionable business themes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        topics_text = response.choices[0].message.content
        return parse_topics_response(topics_text)
    
    except Exception as e:
        print(f"Error extracting topics: {e}")
        return []

def create_opening_remarks_prompt(text: str, company_name: str) -> str:
    """Create prompt for opening remarks topic extraction."""
    return f"""
    Analyze the following opening remarks from {company_name}'s earnings call and extract 3-5 key business topics.
    
    Focus on:
    - Financial performance metrics and results
    - Strategic initiatives and business updates
    - Market conditions and outlook
    - Operational highlights
    - Forward-looking statements and guidance
    
    Avoid generic topics. Be specific to the company and industry.
    
    Text to analyze:
    {text[:3000]}...
    
    Return the topics as a JSON array with this format:
    [
        {{"topic": "Topic Name", "description": "Brief description of the topic"}},
        {{"topic": "Topic Name", "description": "Brief description of the topic"}}
    ]
    """

def create_qa_prompt(text: str, company_name: str) -> str:
    """Create prompt for Q&A section topic extraction."""
    return f"""
    Analyze the following Q&A section from {company_name}'s earnings call and extract 3-5 key business topics.
    
    Focus on:
    - Analyst concerns and questions
    - Management responses and clarifications
    - Financial guidance and outlook
    - Strategic priorities and challenges
    - Market opportunities and risks
    
    Avoid generic topics. Be specific to the company and industry.
    
    Text to analyze:
    {text[:3000]}...
    
    Return the topics as a JSON array with this format:
    [
        {{"topic": "Topic Name", "description": "Brief description of the topic"}},
        {{"topic": "Topic Name", "description": "Brief description of the topic"}}
    ]
    """

def parse_topics_response(response_text: str) -> List[Dict[str, str]]:
    """Parse the AI response into topic dictionaries."""
    try:
        # Try to extract JSON from the response
        import re
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            topics_data = json.loads(json_match.group())
            return topics_data
        else:
            # Fallback: parse manually
            return parse_topics_manually(response_text)
    except Exception as e:
        print(f"Error parsing topics response: {e}")
        return parse_topics_manually(response_text)

def parse_topics_manually(response_text: str) -> List[Dict[str, str]]:
    """Manually parse topics if JSON parsing fails."""
    topics = []
    lines = response_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and ('topic' in line.lower() or 'description' in line.lower()):
            # Try to extract topic and description
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    topic = parts[0].strip().replace('"', '').replace("'", '')
                    description = parts[1].strip().replace('"', '').replace("'", '')
                    if topic and description:
                        topics.append({
                            "topic": topic,
                            "description": description
                        })
    
    return topics[:5]  # Limit to 5 topics

def generate_topic_summary(topic: str, section_text: str, section_type: str, company_name: str) -> str:
    """
    Generate a 2-4 sentence summary for a specific topic.
    """
    client = get_openai_client()
    
    prompt = f"""
    Generate a 2-4 sentence business-focused summary for the topic "{topic}" from {company_name}'s earnings call {section_type} section.
    
    Requirements:
    - Include specific metrics, data points, and insights
    - Capture management perspectives and forward-looking statements
    - Maintain factual accuracy from the source content
    - Focus on business implications and strategic importance
    
    Section text to analyze:
    {section_text[:2000]}...
    
    Return only the summary text, no additional formatting.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a financial analyst expert at creating concise, business-focused summaries from earnings call content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error generating summary for topic {topic}: {e}")
        return f"Summary for {topic} could not be generated at this time."

def process_section_topics(section_text: str, section_type: str, company_name: str) -> Dict[str, Any]:
    """
    Process a section to extract topics and generate summaries.
    """
    # Extract topics
    topics = extract_topics_from_section(section_text, section_type, company_name)
    
    # Generate summaries for each topic
    topic_summaries = []
    for topic_data in topics:
        topic_name = topic_data.get("topic", "")
        topic_description = topic_data.get("description", "")
        
        summary = generate_topic_summary(topic_name, section_text, section_type, company_name)
        
        topic_summaries.append({
            "topic": topic_name,
            "description": topic_description,
            "summary": summary
        })
    
    return {
        "section_type": section_type,
        "topics": topic_summaries,
        "total_topics": len(topic_summaries)
    }
