import json
import time
import toml
import os
from pathlib import Path
from code.prompts import PromptLoader

class ContextGenerator:
    def __init__(self, prompt_path="data/prompts.yaml"):
        self.loader = PromptLoader(prompt_path)

    def generate_context(self, input_path, output_path, llm_client, window_size=3, model='gpt-4.1-mini'):
        data = json.loads(Path(input_path).read_text())
        context_dict = dict()
        root_chapter_ix = 0
        for index, chunk in enumerate(data):
            if index in context_dict.keys():
                continue
            if chunk[0] == 1:
                root_chapter_ix = index
            if 3*len(chunk[1]) > len(chunk[-1]):
                continue
            paragraph_start = max(root_chapter_ix, index - window_size)
            paragraph_end = min(index + window_size + 1, len(data))
            paragraph_list = [ d[-1] for d in data[paragraph_start:paragraph_end]]
            paragraphs = '\n'.join(paragraph_list)
            prompt = self.loader.render(
                "context_extension",
                chunk=chunk[-1],
                neighbors=paragraphs
            )
            time.sleep(2)
            response = llm_client.chat.completions.create(
                model=model,
                messages=[{'role': 'user', 'content': prompt }]
            )
            context_dict[index] = response.choices[0].message.content
        with open(output_path, mode='w+') as f_out:
            f_out.write(json.dumps(context_dict, indent=2))
        return context_dict
