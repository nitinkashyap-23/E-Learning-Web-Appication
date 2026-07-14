import json
import os
import re
import urllib.request
import urllib.error


def generate_questions_for_course(course_title, course_description, assessment, num_questions=25):
    """
    Uses Google Gemini REST API directly (no SDK issues).
    Saves questions directly into the database as AIQuestion objects.
    Returns (success: bool, message: str)
    """

    from study.models import AIQuestion

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return False, "GEMINI_API_KEY not found in .env file"

    prompt = f"""You are an expert educator. Generate exactly {num_questions} multiple choice questions for a course.

Course Title: {course_title}
Course Description: {course_description}

RULES:
- Each question must have exactly 4 options
- One option must be clearly correct
- Cover different difficulty levels: Easy, Medium, Hard
- Cover different topics from the course
- Questions must be factual and educational

Respond ONLY with a valid JSON array. No explanation, no markdown, no extra text.
Format:
[
  {{
    "question": "What is ...?",
    "option1": "Answer A",
    "option2": "Answer B",
    "option3": "Answer C",
    "option4": "Answer D",
    "correct_answer": "Answer A",
    "topic": "Topic Name",
    "difficulty": "Easy"
  }}
]

Generate all {num_questions} questions now:"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    payload = json.dumps({
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

        raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()

        # Clean markdown code fences if present
        raw_text = re.sub(r"^```json\s*", "", raw_text)
        raw_text = re.sub(r"^```\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)
        raw_text = raw_text.strip()

        questions_data = json.loads(raw_text)

        # Delete old questions for this assessment
        AIQuestion.objects.filter(assessment=assessment).delete()

        saved = 0
        for q in questions_data:
            AIQuestion.objects.create(
                assessment=assessment,
                question=q.get("question", ""),
                option1=q.get("option1", ""),
                option2=q.get("option2", ""),
                option3=q.get("option3", ""),
                option4=q.get("option4", ""),
                correct_answer=q.get("correct_answer", ""),
                topic=q.get("topic", "General"),
                difficulty=q.get("difficulty", "Medium"),
            )
            saved += 1

        return True, f"Successfully generated and saved {saved} questions for '{course_title}'"

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        return False, f"API error {e.code}: {error_body}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON from Gemini: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"