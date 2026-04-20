import os
from dotenv import load_dotenv

load_dotenv(override=True)

# 2. IMPORT LANGSMITH AND LOCAL MODULES SECOND
from langsmith import Client
from langsmith.evaluation import evaluate
from src.graph import build_graph
client = Client()

# --- 1. THE EVALUATORS ---

def gemma_extraction_evaluator(run, example):
    """Asserts that the local SLM found the correct architectural flaw."""
    # Grab the final LangGraph state
    final_state = run.outputs
    findings = final_state.get("findings", [])
    
    expected_flaw = example.inputs["expected_flaw"]
    
    # Hunt through the JSON array Gemma generated
    for finding in findings:
        if finding["flaw_type"] == expected_flaw:
            return {"key": "Gemma_Extraction", "score": 1, "comment": f"PASS: Found {expected_flaw}"}
            
    return {"key": "Gemma_Extraction", "score": 0, "comment": f"FAIL: Missed {expected_flaw}"}


def gemini_synthesis_evaluator(run, example):
    """Asserts that the cloud LLM didn't drop the flaw in the final report."""
    final_state = run.outputs
    
    # Safely extract the text whether it's an AIMessage object, a string, or missing
    strategy_raw = final_state.get("strategy", "")
    if hasattr(strategy_raw, "content"):
        strategy_text = strategy_raw.content
    else:
        strategy_text = str(strategy_raw)
    
    expected_flaw = example.inputs["expected_flaw"]
    
    # A simple string inclusion assert
    if expected_flaw.replace("_", " ").lower() in strategy_text.lower():
        return {"key": "Gemini_Synthesis", "score": 1, "comment": "PASS: Included in final strategy"}
        
    return {"key": "Gemini_Synthesis", "score": 0, "comment": "FAIL: Dropped from final strategy"}

# --- 2. THE TEST EXECUTION ---
def run_tests():
    dataset_name = "Architectural_Flaws_Golden_Dataset"
    
    # 1. FORCE RECREATE DATASET (To clear out any bad test data)
    try:
        client.delete_dataset(dataset_name=dataset_name)
    except Exception:
        pass # It didn't exist, which is fine

    print(f"☁️ Creating fresh dataset: {dataset_name}")
    dataset = client.create_dataset(dataset_name=dataset_name)
    
    # Upload our Golden Examples
    client.create_examples(
        inputs=[
            {"file_queue": ["messy_codebase/legacy_controller.py"], "expected_flaw": "SRP Violation"},
            {"file_queue": ["messy_codebase/order_workflow.py"], "expected_flaw": "Method Doing Too Much"}
        ],
        dataset_id=dataset.id
    )

    # 2. Initialize the graph
    app = build_graph()

    # 3. Define the Predict runner
    def predict(inputs):
        # NOTE: If your main.py used a different key (like "files"), change "queue" below to match!
        # We use list() to create a strict copy so .pop() doesn't mutate LangSmith data
        file_list = list(inputs.get("file_queue", [])) 
        
        state = {
            "file_queue": file_list, 
            "current_file": None, 
            "findings": [],
            "migration_strategy": ""
        }
        
        # DEBUG PRINT: Let's prove exactly what is entering the graph
        print(f"\n--- INJECTING STATE: {state} ---")
        
        return app.invoke(state)

    print("🚀 Launching Map-Reduce Evals...")
    
    evaluate(
        predict,
        data=dataset_name, 
        evaluators=[gemma_extraction_evaluator, gemini_synthesis_evaluator],
        experiment_prefix="local-arch-review-evals"
    )

if __name__ == "__main__":
    run_tests()