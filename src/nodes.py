import json
import re
#from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from src.state import GraphState, FileFindings
import gc
import sys
import mlx.core as mx
from mlx_lm import load, generate

# L1: Local Triage & Security Node
# We use temperature 0.0 for deterministic code review
#local_llm = ChatOllama(model="gemma2:9b", temperature=0.0).with_structured_output(FileFindings)
# Swap out ChatOllama for the MLX backend
local_llm = ChatOpenAI(
    base_url="http://localhost:8080/v1",
    api_key="not-needed", # Local servers don't need real keys
    model="mlx-community/gemma-2-9b-it-4bit",
    temperature=0.0,
    max_tokens=2048,
    model_kwargs={"response_format": {"type": "json_object"}}
    )

# Initialize your second LLM (The Reviewer)
# reviewer_llm = ChatOpenAI(
#     base_url="http://localhost:8081/v1", # Note the different port
#     api_key="not-needed",
#     model="mlx-community/Llama-3.1-8B-Instruct-4bit",
#     temperature=0.0
# )
    
    # LangChain handles the Pydantic structured output natively here too!
structured_llm = local_llm.with_structured_output(FileFindings)
# L2: Cloud Architect Node
cloud_llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0.2)


def pop_file_node(state: GraphState):
    """Pops the next file; routes to Gemini if queue is empty."""
    queue = state.get("file_queue", [])
    if not queue:
        return {"current_file": None}
    
    current = queue.pop(0)
    print(f"-> Processing: {current}")
    return {"file_queue": queue, "current_file": current}


def semantic_router_node(state: GraphState):
    file_path = state["current_file"]
    
    # 1. Peek at the file (First 100 characters)
    with open(file_path, "r", encoding="utf-8") as f:
        content_peek = f.read(100)

    print(f"🔍 Routing: {file_path}")
    
    # 2. Use the 1B 'Pico' model
    model_path = "mlx-community/Llama-3.2-1B-Instruct-4bit"

    try:
        print(f"📡 Attempting to load model: {model_path}...")
        # Loading might take time if downloading or converting weights
        model, tokenizer = load(model_path)
        print("✅ Model loaded successfully on Apple Silicon GPU.")
    
    except MemoryError:
        print("❌ Error: Out of Memory. Close other apps (like Chrome or Docker) and try again.")
        sys.exit(1)

    except ConnectionError:
        print("❌ Error: Could not connect to Hugging Face. Check your internet connection.")
        sys.exit(1)

    except Exception as e:
        print(f"❌ An unexpected error occurred while loading the model: {e}")
        # This catches things like 'Model not found' or 'Corrupted files'
        sys.exit(1)

    messages = [
        {
            "role": "system",
            "content": "You are a code filter. Your goal is to find files with logic. Output ONLY 'ANALYZE' or 'SKIP'."
        },
        {
            "role": "user",
            "content": f"""
        Classify these examples:
        1. 'import os\nAPI_KEY = "123"' -> SKIP
        2. 'def process_order(data):\n  if data.valid:...' -> ANALYZE
        3. 'class UserProfile:\n  def __init__(self)...' -> ANALYZE
        4. '# Settings\nDEBUG = True' -> SKIP

        Now classify this code:
        {content_peek}
        
        If it contains ANY functions (def) or classes (class), you MUST output 'ANALYZE'. 
        When in doubt, output 'ANALYZE'.
        """
        }
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    try:
        decision = generate(model, tokenizer, prompt=prompt, max_tokens=100).strip().upper()
        
        # 3. Clean the response (sometimes it adds punctuation)
        if "ANALYZE" in decision:
            print("🚀 Result: ANALYZE - Proceeding to Critique.")
            return {"router_decision": "analyze"}
        else:
            print("🛑 Result: SKIP - Moving to next file.")
            return {"router_decision": "skip"}
            
    finally:
        # Flush memory immediately
        del model
        del tokenizer
        gc.collect()
        mx.metal.clear_cache()


def local_critique_node(state: GraphState):
    """Local SLM reads the file, redacts IP, and flags flaws."""
    file_path = state["current_file"]
    
    with open(file_path, "r", encoding="utf-8") as f:
        code_content = f.read()

    prompt = f"""[INST] <<SYS>>
    You are a JSON-only generator. You MUST return ONLY a valid JSON object matching the schema. 
    DO NOT include any conversational text, introductions, or markdown formatting outside the JSON.
    <</SYS>>
    
    You are a Principal Software Architect reviewing a codebase.
    Review this code from {file_path}.
    Identify flaws based ONLY on these strict architectural categories:

    1. SRP Violation: Class/module doing UI, Data, and Network simultaneously.
    2. Method Doing Too Much: A function that should be broken into 2-3 smaller functions.
    3. Duplication: Logic that seems like it should be imported from a generic utils file.
    4. Broken Polymorphism: Heavy if/elif type-checking instead of using interfaces/abstract classes.
    5. Infra Coupling: Business logic directly instantiating DB connections or raw HTTP requests without injection.
    6. Broken Idempotency: Operations (like charging money) that will cause duplicate state if called twice accidentally.
    7. Non-Deterministic Output: Network calls or external I/O without timeouts, retries, or fallback logic.
    8. Context Bloat: Passing massive objects (like full HTTP requests) when a function only needs 1 or 2 specific strings.
    9. Missing Validation: Accepting raw inputs into DBs or sensitive functions without checking constraints.
    10. Silent Error: Broad 'except' blocks that pass or fail silently.
    11. Broken Encapsulation: Directly accessing private internal variables of another class.
    Return the result strictly in this format:
    {{"flaws": [{{ "flaw_type": "...", "description": "..." }}]}}
    [/INST]
    Code to review:
    {code_content}
"""

    # Look how clean this is compared to the MLX JSON-forcing
    # Following code for ollama - commenting this out for mlx
    # structured_response = local_llm.invoke(prompt)
    
    # Convert Pydantic objects back to dicts for LangGraph state appending
    # flaws_as_dicts = [flaw.model_dump() for flaw in structured_response.flaws]
    
    #return {"findings": flaws_as_dicts}
    raw_response = local_llm.invoke(prompt)
    content = raw_response.content
    # 1. THE BULLETPROOF JSON EXTRACTOR
    # Find the first '{' and the last '}' 
    start_idx = content.find('{')
    end_idx = content.rfind('}')
    
    if start_idx != -1 and end_idx != -1:
        clean_json = content[start_idx:end_idx+1]
    else:
        clean_json = "{}" # Fallback if no brackets are found

    try:
        # Manually parse and validate into your Pydantic model
        data = json.loads(clean_json)
        # INJECT THE FILE NAME PROGRAMMATICALLY!
        for flaw in data.get("flaws", []):
            flaw["file_name"] = file_path
        structured_response = FileFindings(**data)
        flaws_as_dicts = [flaw.model_dump() for flaw in structured_response.flaws]
    except Exception as e:
        print(f"⚠️ Parsing failed. Error: {e}")
        print("⚠️ Raw output omitted to reduce data exposure in logs.")
        
        # 2. THE REDUCER FIX
        # If it fails, pass the raw text as a finding so Gemini still sees it, 
        # instead of returning the state (which causes duplicates) or [] (which loses data).
        fallback_flaw = [{"flaw_type": "Parsing Error", "description": content}]
        return {"findings": fallback_flaw, "current_file": None}

     
        #"findings": state["findings"] + flaws_as_dicts,
    return {"findings": flaws_as_dicts, "current_file": None}



def reflection_node(state: GraphState):
    """The 'Senior Architect' node that prunes false positives."""
    findings = state["findings"]
    print(f"DEBUG: Reflection node started with {len(findings)} findings.")
    if not findings:
        return {"findings": []}

    print("🧠 Reflection Node: Loading Llama-3.2-3B...")
    
    model_path = "mlx-community/Llama-3.2-3B-Instruct-4bit"

    try:
        print(f"📡 Attempting to load model: {model_path}...")
        # Loading might take time if downloading or converting weights
        model, tokenizer = load(model_path)
        print("✅ Model loaded successfully on Apple Silicon GPU.")

    except MemoryError:
        print("❌ Error: Out of Memory. Close other apps (like Chrome or Docker) and try again.")
        sys.exit(1)

    except ConnectionError:
        print("❌ Error: Could not connect to Hugging Face. Check your internet connection.")
        sys.exit(1)

    except Exception as e:
        print(f"❌ An unexpected error occurred while loading the model: {e}")
        # This catches things like 'Model not found' or 'Corrupted files'
        sys.exit(1)

    # 1. Structure as a strict Chat Template (CRITICAL for Llama 3)
    messages = [
        {"role": "system", "content": "You are a Principal Software Architect. You only output raw, valid JSON. No markdown, no explanations, no code blocks."},
        {"role": "user", "content": f"""Review the findings of a Junior Architect.
Code Context: {state.get('last_code_context', 'See original file')}

Previous Findings: {json.dumps(findings, indent=2)}

Determine if each finding is a TRUE POSITIVE or FALSE POSITIVE.
Return ONLY the genuinely problematic findings in this strict JSON format:
{{"vetted_findings": [ ... ]}}
"""}
    ]

    # 2. Apply the template to inject Llama's control tokens
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    try:
        response = generate(model, tokenizer, prompt=prompt, max_tokens=1500)
        print(f"DEBUG: Raw Llama Output: {response[:150]}...") # Lets you see what it actually generated
        
        # 3. Bulletproof JSON Extraction (Regex beats Markdown)
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            clean_json = match.group(0)
            parsed_data = json.loads(clean_json)
            
            # Safely extract the list (handling if model named it vetted_findings or findings)
            vetted = parsed_data.get("vetted_findings", parsed_data.get("findings", []))
            print(f"✅ Reflection success! Kept {len(vetted)} out of {len(findings)} findings.")
            return {"findings": vetted}
        else:
            print("⚠️ Regex found no JSON brackets. Falling back to original findings.")
            return {"findings": findings}

    except json.JSONDecodeError as e:
        print(f"❌ JSON Parsing failed: {e}")
        return {"findings": findings}
    except Exception as e:
        print(f"❌ Reflection failed: {e}")
        return {"findings": findings}

    finally:
        # THE RAM FLUSH
        del model
        del tokenizer
        gc.collect()
        mx.metal.clear_cache()
        print("🧹 Memory flushed.")

def gemini_strategy_node(state: GraphState):
    """Cloud LLM synthesizes the redacted data."""
    findings = state.get("findings", [])
    
    prompt = f"""You are a Fractional CTO. 
Our local security pipeline has scanned the codebase, redacted IP, and extracted these flaws:
{findings}

Synthesize a 3-phase refactoring strategy. You only have access to these sanitized summaries."""

    response = cloud_llm.invoke(prompt)
    return {"migration_strategy": response.content}
