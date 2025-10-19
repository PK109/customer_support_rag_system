import pymupdf, pymupdf4llm
import regex as re
import json
import unicodedata
import difflib
import os

class PDFToMarkdown:
    def __init__(self, input_filepath, image_path="data/images", margins=(50,75)):
        self.input_filepath = input_filepath
        self.output_filepath = os.path.splitext(self.input_filepath)[0] +'.txt'
        self.image_path = image_path
        self.margins = margins
        self.doc = pymupdf.open(input_filepath)
        self.my_headers = pymupdf4llm.TocHeaders(self.doc) # type: ignore
        self.content_first_page = self.doc.get_toc()[0][-1] - 1 # type: ignore
        self.md = ""
        self.output = ""
        # markers used when writing metadata into top of the text file
        self._meta_start = "<!--METADATA_START-->"
        self._meta_end = "<!--METADATA_END-->"

    def extract_markdown(self):
        for page in self.doc[self.content_first_page : self.doc.page_count]:
            clusters = page.cluster_drawings()
            for bb in clusters:
                page.draw_rect(bb, width=0.2)# type: ignore
            self.md += pymupdf4llm.to_markdown(
                self.doc,
                pages=[page.number],
                margins=self.margins,
                hdr_info=self.my_headers,
                write_images=True,
                image_path=self.image_path,
                force_text=False
            )
        return self.md
    

    def export_json(self, toc):
        out_path = os.path.splitext(self.input_filepath)[0] + '_content.json'
        os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(toc, f, ensure_ascii=False, indent=2)
        return toc


    def save_text(self, toc, out_path: str | None = None):
        """Write a text file with the markdown/content.
        """
        out_path = out_path or self.output_filepath
        os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)

        with open(out_path, 'w', encoding='utf-8') as f:
            # write the textual content (joined output chunks or raw md)
            if self.output:
                f.write('\n\n'.join(self.output))
            else:
                f.write(self.md)
    

    def save_metadata(self, out_path: str | None = None):
        meta = self.doc.metadata or {}
        meta['page_count'] = self.doc.page_count
        try:
            meta['toc'] = self.doc.get_toc() # type: ignore
        except Exception:
            meta['toc'] = []
        out_path = out_path or os.path.splitext(self.input_filepath)[0] + f'_meta.json'
        os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"Wrote metadata to {out_path}")


    def clean_markdown(self):
        pattern = r"[^a-zA-Z0-9!@#$%^&*()_\-+=\[\]{}|;:'\",.<>/?\\` \t\n□△◇：±℃φ×Ω（）]"
        self.md = re.sub(pattern, "", self.md)

    def split_markdown(self):
        self.output = re.split(r'\n(?=#)', self.md)
        self.output = [re.sub(r'^#+\s','',text) for text in self.output]


    def build_chunk_dict(self):
        chunk_dict = { chunk.split('\n',1)[0] : chunk for chunk in self.output}
        return chunk_dict

    def match_toc(self, chunk_dict):
        toc = self.doc.get_toc() # type: ignore

        def normalize_text(s: str) -> str:
            """Normalize unicode, remove punctuation/symbols and collapse whitespace."""
            if s is None:
                return ""
            # normalize fullwidth vs ascii, combine characters consistently
            s = unicodedata.normalize("NFKC", s)
            s = s.strip().lower()
            # remove punctuation and symbol characters, keep letters/numbers/spaces
            s = re.sub(r"[\p{P}\p{S}]", "", s)
            s = re.sub(r"\s+", " ", s)
            return s

        # helper to try to find a single best match for a title
        def find_best_match(title: str, candidates: list, threshold: float = 0.80):
            norm_title = normalize_text(title)
            if not candidates:
                return None
            # first try simple substring match on normalized text
            substring_matches = [item for item in candidates if norm_title in normalize_text(item[0]) or normalize_text(item[0]) in norm_title]
            if len(substring_matches) == 1:
                return substring_matches[0]
            if len(substring_matches) > 1:
                # ambiguous: fall through to fuzzy scoring
                pass

            # compute similarity scores and pick best
            scores = []
            for key, val in candidates:
                score = difflib.SequenceMatcher(None, norm_title, normalize_text(key)).ratio()
                scores.append((key, val, score))
            best = max(scores, key=lambda x: x[2])
            if best[2] >= threshold:
                return (best[0], best[1])
            return None

        retries = []
        # First pass: strict/substring or high-threshold fuzzy matching
        for chapter in toc:
            title = chapter[1]
            candidates = list(chunk_dict.items())
            match = find_best_match(title, candidates, threshold=0.80)
            if match is not None:
                key, content = match
                chapter.append(content)
                chunk_dict.pop(key)
            else:
                retries.append(chapter)

        # Second pass: try again with a lower threshold for the remaining chapters
        still_retry = []
        for chapter in retries:
            title = chapter[1]
            candidates = list(chunk_dict.items())
            match = find_best_match(title, candidates, threshold=0.70)
            if match is not None:
                key, content = match
                chapter.append(content)
                chunk_dict.pop(key)
            else:
                still_retry.append(chapter)

        # If anything remains unmatched, fail with a message showing leftovers
        assert len(chunk_dict) == 0, f"Unmatched chunks remain: {list(chunk_dict.keys())}"
        return toc


    def run(self):
        self.extract_markdown()
        self.save_metadata()
        self.clean_markdown()
        self.split_markdown()
        chunk_dict = self.build_chunk_dict()
        toc = self.match_toc(chunk_dict)
        # export matched toc as JSON file (existing behavior) with metadata
        # for later reading/parsing with read_text_with_metadata
        self.export_json(toc)
        return toc
