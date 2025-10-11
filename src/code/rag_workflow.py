from search import Search
from prompts import PromptLoader
from model_setup import setup_model, setup_llm_client

def llm(client, prompt, model='gpt-5-nano'):
    response = client.chat.completions.create(
        model=model,
        messages=[{'role': 'user', 'content': prompt }]
    )
    return response.choices[0].message.content

def refine_query(query, client, query_count, verbose = False) -> list[str]:
    loader = PromptLoader("data/prompts.yaml") 
    prompt = loader.render(
        "refine_query",
        query=query,
        query_count=query_count
    )
      
    llm_queries = []
    trials_count = 0
    while len(llm_queries) != query_count :
        trials_count += 1
        if trials_count >= 3:
            break
        llm_queries = llm(client,prompt).split("\n")
    if verbose:
        print(f"Prompt:\n{prompt}")
        print(f"Refined queries:", *llm_queries, sep="\n")        
    return llm_queries
    
def rag(query, secrets_path, collection, verbose_search=False, verbose_prompt=False):
    loader = PromptLoader("data/prompts.yaml") 
    llm_client = setup_llm_client(secrets_path=secrets_path)
    searcher = Search(model=setup_model(),
                    collection_name=collection, model_name="all-mpnet-base-v2", 
                    history_storage="./data/search_history.jsonl",
                    secrets_path=secrets_path)

    llm_queries = refine_query(query, llm_client, 2)
    search_set = set()
    search_results = []
    llm_queries.append(query)
    for q in llm_queries:
        print("Query: ", q)
        results = searcher.rrf_search(q, 5)
        result_ids = set([p.id for p in results])
        unique_ids = result_ids - search_set
        for result in results:
            if result.id in unique_ids: #avoid duplicates to be sent to LLM
                search_results.append(result)
        search_set.update(result_ids) 
    if verbose_search:
        print(len(search_results), "results in total search\n")
        print("Query search results:")
        print(*search_results, sep="\n\n")
    prompt = loader.build_prompt(query, search_results)
    if verbose_prompt:
        print("\n\nQuery prompt output:")
        print(prompt)
    message = llm(llm_client, prompt)
    return message