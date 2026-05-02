import requests
import json
import time

url = "http://localhost:11434/api/generate"

# Schema definition used to constraint LLM output.
# This is a temporary contract during scripting phase.
ErrorSchema = {
    "root_cause":"string",
    "suggested_fix":"string"
}
# Prompt construction
# Note: This is a simple concatenation approach for now.
# In production, this should be structured into system/task/input sections.
system_role = "You are an expert java debugger assistant"
task = "extract the root cause and suggest a fix for it"
error = "Database connection refused: timeout 30000ms"
constraint = "Respond only in valid JSON matching this schema"
schema = json.dumps(ErrorSchema, indent= 2)
prompt = f"{system_role}\n\n{task}\n\n{error}\n\n{constraint}\n\n{schema}"
print(prompt)
# Model configurations
# - temperature=0 ensures deterministic output.
# - format=json forces structured response
model = 'mistral'
payload = {
    'model':model,
    'prompt':prompt,
    'stream':False,
    'format':'json',
    'options':{
        "temperature": 0
    }
}

# Retry configuration
# Using exponential backoff to simulate resillience againt transient failures
wait_time = 1
max_attempts = 4

# Intential low timeout to force failure for testing retry logic
time_out = 0.001
for attempt in range(max_attempts):
    try:
        # For all attempts except the last, uses a very low timout to trigger failure
        if attempt != max_attempts-1:
            response = requests.post(url, json=payload, timeout=time_out)
            print("success")
            print(response.json())
            break
        else:
            # Final attempt uses a realistic timeout to allow recovery
            response = requests.post(url, json=payload, timeout=30)
            print("success")
            print(response.json())
            break
    except  requests.exceptions.Timeout as err:
        # Exponential backoff: wait_time doubles after each failure
        time.sleep(wait_time)
        print(err)
        print(f"wait {wait_time} second")
        wait_time *= 2
    except requests.exceptions.ConnectionError:
        # Handles the case where the ollama daemon is not reachable at all
        print("Server couldn't be reached")
        break

