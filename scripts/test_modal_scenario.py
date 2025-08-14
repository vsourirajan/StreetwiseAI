#!/usr/bin/env python3
"""
Test script for Modal scenario processing functions with Llama 3.
This script tests the LLM orchestration pipeline locally.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from citybrain.retrieval.scenario import build_scenario_packet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_scenario_packet_building():
    """Test the scenario packet building functionality."""
    print("Testing Scenario Packet Building")
    print("=" * 50)
    
    # Test query
    test_query = "If we pedestrianize Broadway from 14th to 34th in NYC, what happens to delivery routes, traffic congestion, and what zoning amendments would be required?"
    
    print(f"Query: {test_query}")
    print("-" * 80)
    
    try:
        # Build the scenario packet
        scenario_packet = build_scenario_packet(test_query)
        
        print("✓ Scenario packet built successfully!")
        print(f"Status: Success")
        print(f"Total data points: {scenario_packet['data_summary']['total_data_points']}")
        
        # Show zoning information
        zoning_info = scenario_packet['zoning_information']
        print(f"\nZoning Information:")
        print(f"  • Relevant text chunks: {zoning_info['total_chunks_found']}")
        print(f"  • Affected districts: {zoning_info['total_districts_in_area']}")
        
        # Show traffic information
        traffic_info = scenario_packet['traffic_information']
        print(f"\nTraffic Information:")
        print(f"  • Traffic count locations: {traffic_info['total_locations_in_area']}")
        
        # Show area of interest
        area_info = scenario_packet['area_of_interest']
        print(f"\nArea of Interest:")
        print(f"  • Description: {area_info['description']}")
        print(f"  • Bounds: {area_info['bounds']}")
        
        # Show sample zoning chunks
        if zoning_info['relevant_text_chunks']:
            print(f"\nSample Zoning Text (first chunk):")
            first_chunk = zoning_info['relevant_text_chunks'][0]
            print(f"  • Source: {first_chunk.get('source', 'Unknown')}")
            print(f"  • Text preview: {first_chunk.get('text', 'No text')[:200]}...")
        
        # Show sample zoning districts
        if zoning_info['affected_zoning_districts']:
            print(f"\nSample Zoning Districts (first 2):")
            for i, district in enumerate(zoning_info['affected_zoning_districts'][:2]):
                print(f"  • District {i+1}: {district}")
        
        # Show sample traffic data
        if traffic_info['traffic_count_locations']:
            print(f"\nSample Traffic Data (first 2):")
            for i, location in enumerate(traffic_info['traffic_count_locations'][:2]):
                print(f"  • Location {i+1}: {location}")
        
        return scenario_packet
        
    except Exception as e:
        print(f"✗ Error building scenario packet: {e}")
        logger.error(f"Error: {e}", exc_info=True)
        return None


def test_llama3_prompt_generation(scenario_packet):
    """Test the Llama 3 prompt generation logic."""
    print("\n\nTesting Llama 3 Prompt Generation")
    print("=" * 50)
    
    if not scenario_packet:
        print("No scenario packet to analyze")
        return
    
    try:
        # Import the prompt generation function
        from citybrain.modal_app import UrbanPlanningLLM
        
        # Create an instance to test prompt generation
        llm = UrbanPlanningLLM()
        
        # Test query
        test_query = "If we pedestrianize Broadway from 14th to 34th in NYC, what happens to delivery routes, traffic congestion, and what zoning amendments would be required?"
        
        # Generate the prompt (without actually running the model)
        prompt = llm._create_urban_planning_prompt(scenario_packet, test_query)
        
        print("✓ Llama 3 prompt generated successfully!")
        
        # Display the prompt structure
        print(f"\nPrompt Length: {len(prompt)} characters")
        print(f"Prompt Preview (first 500 chars):")
        print("-" * 50)
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        
        # Show what data was included
        zoning_chunks = scenario_packet.get("zoning_information", {}).get("relevant_text_chunks", [])
        zoning_districts = scenario_packet.get("zoning_information", {}).get("affected_zoning_districts", [])
        traffic_data = scenario_packet.get("traffic_information", {}).get("traffic_count_locations", [])
        
        print(f"\nData Included in Prompt:")
        print(f"  • Zoning chunks: {len(zoning_chunks)}")
        print(f"  • Zoning districts: {len(zoning_districts)}")
        print(f"  • Traffic locations: {len(traffic_data)}")
        
        return prompt
        
    except Exception as e:
        print(f"✗ Error generating prompt: {e}")
        logger.error(f"Error: {e}", exc_info=True)
        return None


def main():
    """Main test function."""
    print("City Brain Urban Planning Simulator - Modal Test with Llama 3")
    print("=" * 70)
    
    # Test 1: Scenario packet building
    scenario_packet = test_scenario_packet_building()
    
    # Test 2: Llama 3 prompt generation
    if scenario_packet:
        prompt = test_llama3_prompt_generation(scenario_packet)
        
        if prompt:
            print("\n" + "=" * 70)
            print("✓ All tests passed! The Modal pipeline with Llama 3 is ready.")
            print("\nNext steps:")
            print("1. Deploy to Modal: modal deploy citybrain/modal_app.py")
            print("2. Test remotely: modal run citybrain/modal_app.py::get_scenario_insights")
            print("3. The app will now use Llama 3 for intelligent urban planning analysis!")
            print("4. Build the frontend to consume these AI-generated insights")
        else:
            print("\n✗ Prompt generation test failed")
    else:
        print("\n✗ Scenario packet test failed")
    
    print("\nTest completed.")
    print("\nNote: This test only validates the prompt generation locally.")
    print("The actual Llama 3 model will run on Modal's GPU infrastructure.")


if __name__ == "__main__":
    main() 