import yaml
from jinja2 import Template

class PromptLoader:
    def __init__(self, path: str = "data/prompts.yaml"):
        with open(path, "r", encoding="utf-8") as f:
            self.prompts = yaml.safe_load(f)


    def render(self, name: str, **kwargs) -> str:
        """Render a named prompt with given variables."""
        template = Template(self.prompts[name])
        return template.render(**kwargs)

    def build_prompt(self, query, search_results):
        context = ""
        for index, payload in enumerate(search_results):
            context += f"{index}) Manual:\t{payload.payload['manual']},\nMain Chapter:\t{payload.payload['main_chapter']}\nChapter:\t{payload.payload['chapter']}\nContent: {payload.payload['content']}\n\n"
        return self.render(
            "assistant_prompt",
            query=query,
            context=context
        )