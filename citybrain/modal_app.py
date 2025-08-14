import modal
import logging
import json
from typing import Dict, Any
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Llama 3 Model Configuration
MODEL_ID = "NousResearch/Meta-Llama-3-8B"
MODEL_REVISION = "315b20096dc791d381d514deb5f8bd9c8d6d3061"

# Create Modal app
app = modal.App("city-brain-urban-planning")

# Base image with dependencies only (no baking)
image = (
    modal.Image
        .debian_slim(python_version="3.11")
        .pip_install([
            "sentence-transformers>=2.2.2",
            "pinecone>=2.2.4",
            "geopandas>=0.14.0",
            "shapely>=2.0.0",
            "fiona>=1.9.5",
            "pandas>=2.0.0",
            "requests>=2.31.0",
            "beautifulsoup4>=4.12.0",
            "fastapi>=0.111.0",
            "uvicorn>=0.30.3",
            "pydantic>=2.7.4",
            "python-dotenv>=1.0.0",
            "transformers==4.49.0",
            "torch==2.6.0",
            "accelerate==1.4.0",
        ])
)

# Inject secrets for Pinecone/HF etc.
SECRET = modal.Secret.from_name("citybrain-env")

# GPU Configuration for Llama 3
GPU_CONFIG = "H100:2"
CACHE_DIR = "/cache"
cache_vol = modal.Volume.from_name("hf-hub-cache", create_if_missing=True)


@app.cls(
    gpu=GPU_CONFIG,
    volumes={CACHE_DIR: cache_vol},
    scaledown_window=60 * 10,
    timeout=60 * 60,
    image=image,
    secrets=[SECRET],
)
@modal.concurrent(max_inputs=15)
class UrbanPlanningLLM:
    """Llama 3 model for generating urban planning insights."""
    
    @modal.enter()
    def setup(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        from huggingface_hub import snapshot_download

        logger.info("Setting up Llama 3 model for urban planning...")
        
        # Download the model to the cache directory
        model_path = snapshot_download(repo_id=MODEL_ID, cache_dir=CACHE_DIR)
        logger.info(f"Model downloaded to: {model_path}")

        # Load model and tokenizer
        model = AutoModelForCausalLM.from_pretrained(MODEL_ID, cache_dir=CACHE_DIR)
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, cache_dir=CACHE_DIR)

        self.pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            model_kwargs={"torch_dtype": torch.bfloat16},
            device_map="auto",
        )
        
        logger.info("✓ Llama 3 model loaded successfully")

    @modal.method()
    def generate_urban_planning_analysis(self, scenario_packet: Dict[str, Any], user_query: str) -> str:
        """Generate urban planning analysis using Llama 3."""
        
        # Create a comprehensive prompt for the LLM
        prompt = self._create_urban_planning_prompt(scenario_packet, user_query)
        
        logger.info("Generating urban planning analysis with Llama 3...")
        
        # Generate response
        response = self.pipeline(
            prompt,
            max_length=2048,
            temperature=0.7,
            do_sample=True,
            pad_token_id=self.pipeline.tokenizer.eos_token_id
        )
        
        generated_text = response[0]['generated_text']
        
        # Extract just the generated part (remove the input prompt)
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):].strip()
        
        logger.info("✓ Generated urban planning analysis")
        return generated_text
    
    def _create_urban_planning_prompt(self, scenario_packet: Dict[str, Any], user_query: str) -> str:
        """Create a comprehensive prompt for urban planning analysis."""
        
        # Extract key information
        zoning_chunks = scenario_packet.get("zoning_information", {}).get("relevant_text_chunks", [])
        zoning_districts = scenario_packet.get("zoning_information", {}).get("affected_zoning_districts", [])
        traffic_data = scenario_packet.get("traffic_information", {}).get("traffic_count_locations", [])
        
        # Build the prompt
        prompt = f"""You are an expert urban planner and city planning consultant with deep knowledge of NYC zoning laws, traffic patterns, and urban development. 

USER QUERY: {user_query}

CONTEXT DATA:
"""
        
        # Add zoning information
        if zoning_chunks:
            prompt += f"\nRELEVANT ZONING REGULATIONS ({len(zoning_chunks)} chunks):\n"
            for i, chunk in enumerate(zoning_chunks[:5]):  # Top 5 most relevant
                prompt += f"Chunk {i+1}:\n{chunk.get('text', 'No text available')}\n"
        
        if zoning_districts:
            prompt += f"\nAFFECTED ZONING DISTRICTS ({len(zoning_districts)} districts):\n"
            for i, district in enumerate(zoning_districts[:3]):  # Top 3 districts
                prompt += f"District {i+1}: {district}\n"
        
        if traffic_data:
            prompt += f"\nTRAFFIC DATA ({len(traffic_data)} locations):\n"
            for i, location in enumerate(traffic_data[:3]):  # Top 3 traffic locations
                prompt += f"Location {i+1}: {location}\n"
        
        prompt += """

Please provide a comprehensive urban planning analysis that includes:

1. KEY INSIGHTS: What are the main findings from the data?
2. RECOMMENDATIONS: What specific actions should be taken?
3. POTENTIAL RISKS: What challenges or negative impacts should be considered?
4. ZONING IMPLICATIONS: What zoning changes or amendments would be required?
5. TRAFFIC IMPACT: How would this affect traffic patterns and what mitigation is needed?
6. NEXT STEPS: What should be done next to move this project forward?

Format your response in a clear, professional manner suitable for city officials and stakeholders.

ANALYSIS:
"""
        
        return prompt


@app.function(
    image=image,
    timeout=120,
    memory=1024,
    cpu=0.5,
    secrets=[SECRET],
)
def get_scenario_insights(user_query: str) -> Dict[str, Any]:
    """
    End-to-end function that processes a user query and returns urban planning insights.
    """
    try:
        logger.info(f"Processing end-to-end scenario: {user_query}")

        # Simple fallback packet for demo; retrieval disabled while baking is off
        parsed = {}
        scenario_packet = {
            "query": user_query,
            "parsed_components": parsed,
            "area_of_interest": {
                "bounds": {"min_lat": 40.7378, "max_lat": 40.7505, "min_lon": -73.9950, "max_lon": -73.9850},
                "description": "Broadway corridor from 14th to 34th Street, Manhattan"
            },
            "zoning_information": {
                "relevant_text_chunks": [],
                "affected_zoning_districts": [],
                "total_chunks_found": 0,
                "total_districts_in_area": 0
            },
            "traffic_information": {
                "traffic_count_locations": [],
                "total_locations_in_area": 0
            },
            "data_summary": {
                "total_data_points": 0,
                "data_types": ["zoning_text", "zoning_districts", "traffic_counts"],
                "geographic_scope": "Manhattan corridor"
            }
        }

        # Process analysis (hardcoded or LLM)
        try:
            logger.info("Initializing Llama 3 model for analysis...")
            llm = UrbanPlanningLLM()
            analysis_text = llm.generate_urban_planning_analysis.remote(scenario_packet, user_query)
            logger.info("Successfully generated analysis text")

            result = {
                "status": "success",
                "query": user_query,
                "analysis": {
                    "summary": f"AI-generated analysis of urban planning scenario: {user_query}",
                    "full_analysis": analysis_text,
                    "model_used": "NousResearch/Meta-Llama-3-8B",
                    "generation_method": "AI-powered urban planning analysis"
                },
                "data_summary": scenario_packet.get("data_summary", {}),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as llm_error:
            logger.error(f"Error calling analysis: {llm_error}")
            result = {
                "status": "error",
                "error": f"Analysis failed: {str(llm_error)}",
                "query": user_query,
                "analysis": {
                    "summary": f"Analysis failed for: {user_query}",
                    "full_analysis": f"Sorry, the analysis encountered an error: {str(llm_error)}. Please try again.",
                    "model_used": "Error - analysis unavailable",
                    "generation_method": "Error occurred during processing"
                },
                "data_summary": scenario_packet.get("data_summary", {}),
                "timestamp": datetime.utcnow().isoformat()
            }

        final_response = {
            "status": "success",
            "query": user_query,
            "scenario_packet": scenario_packet,
            "llm_analysis": result,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"Returning final response with status: {final_response['status']}")
        logger.info(f"Response structure: {list(final_response.keys())}")
        print(json.dumps(final_response, indent=2))
        return final_response

    except Exception as e:
        logger.error(f"Error in end-to-end scenario processing: {e}")
        error_response = {
            "status": "error",
            "error": str(e),
            "query": user_query,
            "timestamp": datetime.utcnow().isoformat()
        }
        print(json.dumps(error_response, indent=2))
        return error_response


@app.function(
    image=image,
    timeout=600,
    memory=4096,
    cpu=2.0
)
def ingest_all_data():
    logger.info("Data ingestion function placeholder (baking disabled)")
    return {"status": "success", "message": "Ingestion placeholder"}


@app.local_entrypoint()
def main():
    print("City Brain Urban Planning Simulator")
    test_query = "If we pedestrianize Broadway from 14th to 34th in NYC, what zoning amendments would be required?"
    result = get_scenario_insights.remote(test_query)
    print(json.dumps(result, indent=2))