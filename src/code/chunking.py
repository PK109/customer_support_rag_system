import math
import re
import json
import pathlib
from transformers import AutoTokenizer

class TextChunker:
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def chunk_text_by_lines(self, text, token_limit):
        lines = text.splitlines(keepends=True)
        chunks, current_chunk, current_tokens = [], [], 0
        all_tokens = self.tokenizer.encode(text, add_special_tokens=False)
        chunk_size = math.ceil(len(all_tokens) / math.ceil(len(all_tokens)/ token_limit))
        for line in lines:
            line_tokens = self.tokenizer.encode(line, add_special_tokens=False)
            if current_tokens + len(line_tokens) > token_limit:
                chunks.append("".join(current_chunk).strip())
                current_chunk, current_tokens = [], 0
            current_chunk.append(line)
            current_tokens += len(line_tokens)
            if current_tokens > chunk_size:
                chunks.append("".join(current_chunk).strip())
                current_chunk, current_tokens = [], 0
        if current_chunk:
            chunks.append("".join(current_chunk).strip())
        return chunks, chunk_size

    def clean_text(self, text):
        notes_pattern = r'Note (?=\d\))'
        text = re.sub(r"-<br\s*/?>", "", text)
        text = re.sub(r"<br\s*/?>", "; ", text)
        text = re.sub(r" +", " ", text)
        text = re.sub(r"\.+", ".", text)
        text = re.sub(r"~", "", text)
        text = re.sub(notes_pattern, " *Note ", text)

        return text

    def chunk_file(self, input_path, output_path, token_limit=300):
        json_read = pathlib.Path(input_path).read_text()
        data = json.loads(json_read)
        chunked_data = []
        for chunk in data:
            try:
                assert len(chunk) == 4, f"Expected 4 elements per chunk, got {len(chunk)} in chapter {chunk[1]}"
                text = self.clean_text(chunk[-1])
            except AssertionError as e:
                print(f"Skipping chunk due to error:\n{e}")
                continue
            chunks, size = self.chunk_text_by_lines(text, token_limit)
            for text_chunk in chunks:
                chunked_data.append([
                    chunk[0],
                    chunk[1],
                    chunk[2],
                    text_chunk
                ])
        with open(output_path, mode='w+') as f_out:
            f_out.write(json.dumps(chunked_data, indent=2))
        return chunked_data
