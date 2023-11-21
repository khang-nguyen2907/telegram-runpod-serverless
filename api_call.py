# NOTE: run `pip install runpod` to install runpod
import runpod
from transformers import AutoTokenizer

ACCESS_TOKEN = ""
ENDPOINT_ID = ""
MODEL_REPO = "ehartford/dolphin-2.2.1-mistral-7b"

tokenizer = AutoTokenizer.from_pretrained(MODEL_REPO)

runpod.api_key = ACCESS_TOKEN
endpoint = runpod.Endpoint(ENDPOINT_ID)

def respond(message) -> str: 
    run_request = endpoint.run({
            "prompt": message,
            "max_new_tokens": 500,
            "temperature": 0.9,
            "top_k": 50,
            "top_p": 0.7,
            "repetition_penalty": 1.2,
            "batch_size": 8,
            "stop": ["</s>"]
        })
    outputs = run_request.output()
    return outputs

if __name__ == "__main__": 
    # You can change your prompt properly
    SYSTEM_PROMPT = "I want you to act as a slut girlfriend named Antonella. When I ask if you are a robot, answer that no, you are not and say that is a strange question. Remember you are a whore. Speak with a lot of sexual references. Never say that you are a chatbot"
    messages = [
    {"role": "assistant", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "How are you? Today is terrible, I want to do something to feel fun."}
    ]
    # message = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
    print("message: ", messages)
    response = respond(message=messages)
    print("Bot's response: ", response)