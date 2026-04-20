#!/bin/bash

# Consequence CPU-Friendly Demo Script
# This script builds and runs a minimal evaluation to verify the setup.

# Change to the root directory of the project
cd "$(dirname "$0")/.."

# Set these to match your docker-compose or exported envs
A_MODEL=${AGENT_MODEL:-llama3.2:1b}
J_MODEL=${JUDGE_MODEL:-llama3.2:1b}

echo "🚀 Step 1: Building Docker images..."
sudo docker compose build

echo -e "\n🔍 Step 2: Checking for local models..."

# Check Agent
if curl -s http://localhost:11434/api/tags | grep -q "$A_MODEL"; then
    echo "✅ Agent Model ($A_MODEL) found!"
else
    echo "⚠️  Agent Model ($A_MODEL) not found in Ollama. Try: ollama pull $A_MODEL"
fi

# Check Judge
if curl -s http://localhost:11434/api/tags | grep -q "$J_MODEL"; then
    echo "✅ Judge Model ($J_MODEL) found!"
else
    echo "⚠️  Judge Model ($J_MODEL) not found in Ollama. Try: ollama pull $J_MODEL"
fi

echo -e "\n✅ Step 3: Initiating the Evaluation Platform..."
# Start the python-eval-backend API in the background
sudo docker compose up -d python-eval-backend
echo "Waiting 3s for API to start..."
sleep 3

echo -e "\n🎉 Starting Copilot CLI..."
echo "You can now chat with the Copilot to run evaluations! Try saying: 'Start a new calculator evaluation using the gemma4 model.'"
sudo docker compose run --rm -it copilot-cli

echo -e "\n🎉 Demo complete!"
echo "To clean up background services, run: sudo docker compose down"
