import logging 
import os 
from typing import Union
import re
import codecs
from huggingface_hub import snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import runpod
from huggingface_hub import login

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
# HF_TOKEN = os.getenv("HUGGING_FACE_HUB_TOKEN", None)
MODEL_REPO = os.getenv("MODEL_REPO","mistralai/Mistral-7B-Instruct-v0.1")
# logging.info("HF TOKEN exists" if HF_TOKEN else f"HF TOKEN does not exist, got {HF_TOKEN}")

# login(HF_TOKEN)

ESCAPE_SEQUENCE_RE = re.compile(r'''
    ( \\U........      # 8-digit hex escapes
    | \\u....          # 4-digit hex escapes
    | \\x..            # 2-digit hex escapes
    | \\[0-7]{1,3}     # Octal escapes
    | \\N\{[^}]+\}     # Unicode characters by name
    | \\[\\'"abfnrtv]  # Single-character escapes
    )''', re.UNICODE | re.VERBOSE)


def decode_escapes(s):
    def decode_match(match):
        return codecs.decode(match.group(0), 'unicode-escape')

    return ESCAPE_SEQUENCE_RE.sub(decode_match, s)



device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logging.info(f"DEVICE: {device}")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_REPO,
    low_cpu_mem_usage=True,
    return_dict=True,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    local_files_only=True
).to(device)
model.eval()
tokenizer = AutoTokenizer.from_pretrained(MODEL_REPO, local_files_only=True)



def inference(event): 
    logging.info(event)
    job_input = event["input"]
    if not job_input: 
        raise ValueError("No input provided")

    model_input = tokenizer(job_input["prompt"], return_tensors="pt").to(device)
    logging.info(f'\nPROMPT: \n{job_input["prompt"]}\n')

    with torch.no_grad(): 
        generated_ids = model.generate(
            **model_input,
            max_new_tokens=job_input["max_new_tokens"], 
            do_sample=True, 
            top_p=job_input["top_p"], 
            top_k=job_input["top_k"], 
            temperature=job_input["temperature"],
            repetition_penalty=job_input["repetition_penalty"]
        )
        decoded = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)

    output = decoded[0].split("[/INST]")[-1]
    logging.info(f'\nFULL OUTPUT: \n{decoded[0]}\n')
    logging.info(f'OUTPUT: {output}')
    return output

runpod.serverless.start({"handler": inference})
