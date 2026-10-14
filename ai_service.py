"""
AI Service integration module for AI Study Assistant.
Supports Google Gemini API, OpenAI-compatible APIs, and a transparent Demo Mode.
Isolates API calls, handles JSON response parsing/validation, timeouts, and error handling.
"""

import json
import re
import requests
from config import Config


class AIServiceError(Exception):
    """Custom exception raised when an AI provider returns an error."""
    pass


def extract_json_from_response(text: str) -> dict:
    """
    Safely extract and parse JSON from AI response text,
    stripping markdown code blocks or surrounding text.
    """
    if not text:
        raise AIServiceError("The AI model returned an empty response.")

    cleaned = text.strip()

    # Match ```json ... ``` blocks
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if json_match:
        cleaned = json_match.group(1).strip()

    # Sometimes models return JSON starting with { or [ with trailing commentary
    if not (cleaned.startswith("{") or cleaned.startswith("[")):
        bracket_start = cleaned.find("{")
        if bracket_start != -1:
            cleaned = cleaned[bracket_start:]

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as err:
        # Try finding the closing bracket
        try:
            bracket_end = cleaned.rfind("}")
            if bracket_end != -1:
                return json.loads(cleaned[:bracket_end + 1])
        except Exception:
            pass
        raise AIServiceError(f"Failed to parse structured JSON from AI output: {err.msg}")


class AIService:
    """Configurable AI service adapter."""

    def __init__(self, provider: str = None, api_key: str = None, model: str = None):
        self.provider = (provider or Config.AI_PROVIDER).lower()
        self.gemini_key = api_key or Config.GEMINI_API_KEY
        self.gemini_model = model or Config.GEMINI_MODEL
        self.openai_key = api_key or Config.OPENAI_API_KEY
        self.openai_model = model or Config.OPENAI_MODEL
        self.timeout = Config.AI_TIMEOUT_SECONDS

    def get_provider_status(self) -> dict:
        """Return provider configuration status without revealing secrets."""
        has_gemini = bool(self.gemini_key and not self.gemini_key.startswith("your_"))
        has_openai = bool(self.openai_key and not self.openai_key.startswith("your_"))

        if self.provider == "gemini":
            is_configured = has_gemini
            active_name = f"Google Gemini ({self.gemini_model})"
        elif self.provider == "openai":
            is_configured = has_openai
            active_name = f"OpenAI ({self.openai_model})"
        else:
            is_configured = False
            active_name = "Demo Mode (Offline Samples)"

        return {
            "provider": self.provider,
            "is_configured": is_configured,
            "active_model": active_name,
            "is_demo": not is_configured
        }

    def generate_text(self, system_prompt: str, user_prompt: str) -> dict:
        """Generate unstructured or markdown text using the active provider."""
        status = self.get_provider_status()

        if status["is_demo"]:
            return self._generate_demo_text(user_prompt)

        if self.provider == "gemini":
            return self._call_gemini_api(system_prompt, user_prompt)
        elif self.provider == "openai":
            return self._call_openai_api(system_prompt, user_prompt)
        else:
            return self._generate_demo_text(user_prompt)

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Generate and validate structured JSON using the active provider."""
        status = self.get_provider_status()

        if status["is_demo"]:
            return self._generate_demo_json(user_prompt)

        if self.provider == "gemini":
            res = self._call_gemini_api(system_prompt, user_prompt, json_mode=True)
        elif self.provider == "openai":
            res = self._call_openai_api(system_prompt, user_prompt, json_mode=True)
        else:
            return self._generate_demo_json(user_prompt)

        parsed_data = extract_json_from_response(res["text"])
        return {
            "data": parsed_data,
            "provider": res["provider"],
            "model": res["model"],
            "is_demo": False
        }

    # ==================== Google Gemini API ====================
    def _call_gemini_api(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> dict:
        """Call Google Gemini REST API."""
        if not self.gemini_key:
            raise AIServiceError("GEMINI_API_KEY is not configured in .env file.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "generationConfig": {
                "temperature": 0.3,
                "topP": 0.95,
                "maxOutputTokens": 3072,
            }
        }

        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout
            )
        except requests.exceptions.Timeout:
            raise AIServiceError("Gemini API request timed out after 45 seconds. Please try again with shorter text.")
        except requests.exceptions.RequestException as e:
            raise AIServiceError(f"Network error connecting to Gemini API: {str(e)}")

        if response.status_code != 200:
            try:
                err_data = response.json()
                msg = err_data.get("error", {}).get("message", response.text)
            except Exception:
                msg = response.text
            raise AIServiceError(f"Gemini API error (HTTP {response.status_code}): {msg}")

        data = response.json()
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                raise AIServiceError("No generation candidates returned from Gemini.")
            text_result = candidates[0]["content"]["parts"][0]["text"]
            return {
                "text": text_result,
                "provider": "gemini",
                "model": self.gemini_model,
                "is_demo": False
            }
        except (KeyError, IndexError) as e:
            raise AIServiceError(f"Unexpected response structure from Gemini: {str(e)}")

    # ==================== OpenAI API ====================
    def _call_openai_api(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> dict:
        """Call OpenAI Chat Completions API."""
        if not self.openai_key:
            raise AIServiceError("OPENAI_API_KEY is not configured in .env file.")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_key}"
        }

        payload = {
            "model": self.openai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 3072
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        except requests.exceptions.Timeout:
            raise AIServiceError("OpenAI API request timed out after 45 seconds.")
        except requests.exceptions.RequestException as e:
            raise AIServiceError(f"Network error connecting to OpenAI API: {str(e)}")

        if response.status_code != 200:
            try:
                err_data = response.json()
                msg = err_data.get("error", {}).get("message", response.text)
            except Exception:
                msg = response.text
            raise AIServiceError(f"OpenAI API error (HTTP {response.status_code}): {msg}")

        data = response.json()
        try:
            text_result = data["choices"][0]["message"]["content"]
            return {
                "text": text_result,
                "provider": "openai",
                "model": self.openai_model,
                "is_demo": False
            }
        except (KeyError, IndexError) as e:
            raise AIServiceError(f"Unexpected response structure from OpenAI: {str(e)}")

    # ==================== High-Quality Offline Demo Mode ====================
    def _generate_demo_text(self, user_prompt: str) -> dict:
        """
        Provides realistic sample outputs when no API key is supplied,
        with a transparent disclaimer banner.
        """
        # Concept Explainer in Telugu
        if "Telugu" in user_prompt or "తెలుగు" in user_prompt:
            text = """# 💡 సింపుల్ డెఫినిషన్ (Simple Definition)
ఈ భావన కంప్యూటర్ సైన్స్ మరియు ఇంజనీరింగ్‌లో అత్యంత కీలకమైన పునాది. ఇది సంక్లిష్ట సమస్యలను సులభంగా అర్థం చేసుకునే పద్ధతిలో విభజించి పరిష్కరిస్తుంది.

# 🪜 దశల వారీ వివరణ (Step-by-Step Breakdown)
1. **మొదటి దశ**: సమస్యను గుర్తించి ఇన్పుట్ మరియు అవుట్పుట్ డేటాను విశ్లేషించడం.
2. **రెండవ దశ**: పరిష్కారానికి అవసరమైన తార్కిక నియమాలను క్రమపద్ధతిలో వర్తింపజేయడం.
3. **మూడవ దశ**: సమర్థవంతమైన ఫలితాన్ని పొందేలా ఆప్టిమైజ్ చేయడం.

# 🌍 నిజ జీవిత ఉదాహరణ (Real-Life Example)
ఒక లైబ్రరీలో పుస్తకాలను వెతకడం లాంటిది. పుస్తకాలు క్రమపద్ధతిలో అమర్చబడి ఉంటే క్షణాల్లో కనుగొనవచ్చు.

# ⭐ గుర్తుంచుకోవాల్సిన ముఖ్యమైన అంశాలు
- ప్రతీ భావనకూ ప్రాథమిక నియమాలు ఉంటాయి.
- సిద్ధాంతం కంటే ప్రాక్టికల్ ప్రాక్టీస్ ఎక్కువ అవగాహన కల్పిస్తుంది.

# ⚠️ సాధారణంగా చేసే తప్పులు (Common Mistakes)
- బేసిక్స్ సరిగ్గా అర్థం చేసుకోకుండా నేరుగా కష్టమైన టాపిక్స్ నేర్చుకోవడానికి ప్రయత్నించడం.

# ⚡ త్వరిత పునర్విమర్శ (Quick Revision)
- నిర్వచనం గుర్తుంచుకోండి
- దశల క్రమాన్ని పాటించండి
- వాస్తవిక ఉదాహరణలతో అనుసంధానించండి

# ❓ అవగాహన పరీక్షించే 3 ప్రశ్నలు
1. ఈ భావన యొక్క ముఖ్య ఉద్దేశ్యం ఏమిటి? *(హింట్: సమస్య పరిష్కారం)*
2. ప్రాథమిక దశలో మొదట ఏం చేయాలి? *(హింట్: ఇన్పుట్ విశ్లేషణ)*
3. నిజ జీవితంలో దీనిని ఎక్కడ వర్తింపజేయవచ్చు? *(హింట్: డేటా నిర్వహణ)*
"""
        elif "Concept to Explain:" in user_prompt:
            # Concept Explainer in English
            match = re.search(r"Concept to Explain:\s*([^\n\r]+)", user_prompt)
            concept_name = match.group(1).strip() if match else "Computer Science Concept"
            text = f"""# 💡 Simple Definition
**{concept_name}** is a core fundamental principle in computer science and technology that allows systems to break complex processes down into predictable, efficient, and reproducible steps.

# 🪜 Step-by-Step Breakdown
1. **Initiation**: The system receives input data or parameters and validates the preconditions.
2. **Processing & Logic Execution**: Core algorithmic operations and transformations are sequentially or concurrently executed.
3. **Termination & Output**: Results are verified against expected constraints and returned in the required format.

# 🌍 Real-Life Example & Analogy
Think of {concept_name} like following a recipe in a restaurant kitchen: even if hundreds of orders arrive, following a structured sequence of prep, cook, and plate guarantees high quality every time.

# ⭐ Important Points to Remember
- Time complexity and space efficiency dictate real-world performance.
- Modularity keeps the design maintainable and testable.
- Consistency and handling edge cases is vital for robust systems.

# ⚠️ Common Mistakes & Misconceptions
- Forgetting edge cases (such as null/empty inputs or boundary conditions).
- Confusing theoretical best-case complexity with average real-world runtime.

# ⚡ Quick Revision Summary
- Clean input → Structured transformation → Verified output.
- Always check base cases and boundary constraints.
- Prioritize code clarity before aggressive micro-optimizations.

# ❓ 3 Check-for-Understanding Questions
1. What is the primary purpose of {concept_name}? *(Hint: Transforming inputs efficiently)*
2. What usually happens if boundary conditions are overlooked? *(Hint: Unexpected errors or crashes)*
3. How does this concept benefit scalable software design? *(Hint: Modularity and predictability)*
"""
        else:
            # Summary
            text = """# 📌 Core Summary (Overview)
The provided study notes present fundamental concepts, architectural workflows, and best practices. Key principles emphasize modularity, systematic problem-solving, and rigorous validation.

# 🔑 Key Points & Concepts
- **Foundational Architecture**: Well-structured design allows applications to scale predictably while minimizing technical debt.
- **Data Flow & Encapsulation**: Clear separation of responsibilities between client interfaces, business logic, and persistent storage.
- **Error Handling & Resilience**: Proactive handling of edge cases and input validation prevents runtime failures.
- **Iterative Testing**: Verification through automated unit tests and user acceptance ensures product quality.

# 📖 Important Definitions & Terminology
- **Modularity**: The degree to which a system's components may be separated and recombined.
- **Active Recall**: A learning technique where memory is stimulated through regular testing and retrieval practice.
- **Algorithmic Complexity**: A metric measuring the computational time and storage required as input size grows.

# 📐 Formulas & Rules
- **Efficiency Metric**: Performance = Work Output / Resource Units Consumed.
- **Spaced Repetition Rule**: Retention improves exponentially when review intervals gradually increase.

# ⚡ Bullet-Point Quick Revision Notes
- Understand the core definition before memorizing edge cases.
- Use structured diagrams to map out complex relationships.
- Solve practice problems within timed constraints for exam readiness.
"""

        return {
            "text": text,
            "provider": "demo",
            "model": "Sample Demo Generator",
            "is_demo": True
        }

    def _generate_demo_json(self, user_prompt: str) -> dict:
        """Generate structured JSON demo data for questions, flashcards, or mock tests."""
        if '"type": "short"' in user_prompt:
            data = {
                "type": "short",
                "questions": [
                    {
                        "id": 1,
                        "question": "Explain the primary objective of data normalization.",
                        "model_answer": "Data normalization reduces data redundancy and improves data integrity by structuring relational tables according to formal rules called normal forms.",
                        "key_points": [
                            "Minimizes duplicate information",
                            "Prevents insertion, update, and deletion anomalies"
                        ],
                        "important_keywords": ["normalization", "redundancy", "data integrity", "normal forms"]
                    },
                    {
                        "id": 2,
                        "question": "What is the difference between synchronous and asynchronous operations?",
                        "model_answer": "Synchronous operations block execution until the task finishes, whereas asynchronous operations run in the background allowing other operations to continue without waiting.",
                        "key_points": [
                            "Synchronous is blocking",
                            "Asynchronous is non-blocking and improves concurrency"
                        ],
                        "important_keywords": ["synchronous", "asynchronous", "blocking", "concurrency"]
                    },
                    {
                        "id": 3,
                        "question": "Define encapsulation in Object-Oriented Programming.",
                        "model_answer": "Encapsulation bundles data attributes and methods that operate on that data into a single unit (class) while restricting direct external access to internal state.",
                        "key_points": [
                            "Bundling data with methods",
                            "Data hiding using access modifiers"
                        ],
                        "important_keywords": ["encapsulation", "class", "data hiding", "access modifiers"]
                    }
                ]
            }
        elif '"type": "long"' in user_prompt:
            data = {
                "type": "long",
                "questions": [
                    {
                        "id": 1,
                        "question": "Analyze the architecture of a full-stack web application, explaining how frontend, backend, database, and external APIs communicate.",
                        "answer_outline": [
                            "I. Client Layer: UI presentation, DOM rendering, and user event handling",
                            "II. Network & Protocol: HTTP/HTTPS REST or WebSocket requests and response lifecycles",
                            "III. Backend Service Layer: Route controllers, business logic validation, and security sanitization",
                            "IV. Persistence & Database Layer: Relational queries, ACID transactions, and index optimization",
                            "V. Third-Party Integrations: Secure API calls with API keys stored in environment variables"
                        ],
                        "main_concepts": ["Client-Server Model", "RESTful Architecture", "Database Transactions", "API Security"],
                        "evaluation_rubric": "Clear architectural diagram, detailed explanation of each layer, and practical mention of security measures like input sanitization and secure environment keys."
                    },
                    {
                        "id": 2,
                        "question": "Compare and contrast Relational (SQL) and Non-Relational (NoSQL) databases, highlighting their performance trade-offs and use cases.",
                        "answer_outline": [
                            "I. Overview of Relational vs NoSQL data models",
                            "II. Schema rigidity vs flexible JSON/document schemas",
                            "III. ACID compliance vs BASE consistency principles",
                            "IV. Vertical vs Horizontal scalability dynamics",
                            "V. Decision matrix and appropriate modern application use cases"
                        ],
                        "main_concepts": ["SQL Tables", "NoSQL Documents", "ACID vs BASE", "Horizontal Scalability"],
                        "evaluation_rubric": "Comprehensive comparison across schema, query language, transaction consistency, scalability, and specific industry examples."
                    }
                ]
            }
        elif '"flashcards":' in user_prompt:
            data = {
                "flashcards": [
                    {
                        "id": 1,
                        "front": "What is the primary function of an Operating System?",
                        "back": "To manage computer hardware and software resources, and provide common services for computer programs (e.g., process management, memory allocation, and file systems).",
                        "category": "Definition"
                    },
                    {
                        "id": 2,
                        "front": "What does ACID stand for in Database Management Systems?",
                        "back": "Atomicity, Consistency, Isolation, and Durability — the four key properties ensuring reliable database transactions.",
                        "category": "Concept"
                    },
                    {
                        "id": 3,
                        "front": "What is Time Complexity in Algorithm Analysis?",
                        "back": "A mathematical characterization of the computational time required to execute an algorithm as a function of the input size (n), commonly represented in Big-O notation.",
                        "category": "Definition"
                    },
                    {
                        "id": 4,
                        "front": "What is the difference between a Process and a Thread?",
                        "back": "A process is an independent executing program with its own memory space; a thread is a lightweight execution unit within a process that shares memory with sibling threads.",
                        "category": "Concept"
                    },
                    {
                        "id": 5,
                        "front": "What is the primary benefit of Spaced Repetition in studying?",
                        "back": "It interrupts the forgetting curve by scheduling reviews at increasing intervals, significantly improving long-term cognitive retention.",
                        "category": "Learning Science"
                    }
                ]
            }
        elif '"test_title":' in user_prompt:
            # Mock test
            data = {
                "test_title": "Comprehensive Mock Examination",
                "difficulty": "Medium",
                "total_questions": 5,
                "questions": [
                    {
                        "id": 1,
                        "question": "Which HTTP status code signifies that a resource was successfully created on the server?",
                        "options": ["200 OK", "201 Created", "204 No Content", "301 Moved Permanently"],
                        "correct_answer": 1,
                        "explanation": "HTTP 201 Created indicates that the request succeeded and led to the creation of a new resource on the server.",
                        "topic": "Web Protocols & REST"
                    },
                    {
                        "id": 2,
                        "question": "What is the worst-case time complexity of standard Binary Search on a sorted array of size n?",
                        "options": ["O(1)", "O(n)", "O(log n)", "O(n log n)"],
                        "correct_answer": 2,
                        "explanation": "Binary search halves the search space with each comparison, yielding O(log n) worst-case time complexity.",
                        "topic": "Algorithms"
                    },
                    {
                        "id": 3,
                        "question": "In relational database design, what is a Primary Key?",
                        "options": [
                            "A key that can accept duplicate null values",
                            "A field or combination of fields that uniquely identifies each record in a table",
                            "An external key that references another table",
                            "A temporary cache key used during queries"
                        ],
                        "correct_answer": 1,
                        "explanation": "A primary key is a unique identifier for each row in a database table. It cannot contain NULL values.",
                        "topic": "Database Systems"
                    },
                    {
                        "id": 4,
                        "question": "Why is storing API keys directly in client-side HTML or JavaScript a severe security risk?",
                        "options": [
                            "It slows down page loading times",
                            "Client-side code is publicly inspectable in the user's browser, exposing secrets to anyone",
                            "JavaScript cannot transmit API keys over HTTPS",
                            "Browsers automatically delete API keys stored in cookies"
                        ],
                        "correct_answer": 1,
                        "explanation": "Frontend source code is transmitted directly to the user's browser where anyone can inspect it or extract credentials using developer tools.",
                        "topic": "Web Security"
                    },
                    {
                        "id": 5,
                        "question": "Which of the following best describes 'Active Recall' as a study technique?",
                        "options": [
                            "Passively re-reading textbook chapters multiple times",
                            "Highlighting lines of text with multiple colored pens",
                            "Actively stimulating memory retrieval through practice questions and flashcards",
                            "Listening to recorded lectures while sleeping"
                        ],
                        "correct_answer": 2,
                        "explanation": "Active recall forces the brain to retrieve information from memory without looking at notes, strengthening neural retention pathways.",
                        "topic": "Learning Science"
                    }
                ]
            }
        else:
            # Default MCQ practice
            data = {
                "type": "mcq",
                "questions": [
                    {
                        "id": 1,
                        "question": "What is the fundamental benefit of modular code organization?",
                        "options": [
                            "It makes code run faster automatically",
                            "It separates concerns, making systems easier to maintain, test, and debug",
                            "It prevents any syntax errors from occurring",
                            "It eliminates the need for database storage"
                        ],
                        "correct_answer": 1,
                        "explanation": "Modularity isolates functionality into independent, cohesive components, improving maintainability and testability.",
                        "topic": "Software Engineering"
                    },
                    {
                        "id": 2,
                        "question": "Which data structure operates on a First-In, First-Out (FIFO) principle?",
                        "options": ["Stack", "Queue", "Binary Search Tree", "Hash Map"],
                        "correct_answer": 1,
                        "explanation": "A Queue processes elements in the exact order they arrived (FIFO), unlike a Stack which is Last-In, First-Out (LIFO).",
                        "topic": "Data Structures"
                    },
                    {
                        "id": 3,
                        "question": "What role does the SQLite database play in a desktop or lightweight web app?",
                        "options": [
                            "It requires a heavy standalone background server daemon",
                            "It provides a self-contained, serverless, zero-configuration relational storage engine",
                            "It replaces the need for a web browser",
                            "It only stores unstructured images"
                        ],
                        "correct_answer": 1,
                        "explanation": "SQLite is an embedded, serverless SQL database engine that reads and writes directly to regular disk files.",
                        "topic": "Databases"
                    }
                ]
            }

        return {
            "data": data,
            "provider": "demo",
            "model": "Sample Demo Generator",
            "is_demo": True
        }
