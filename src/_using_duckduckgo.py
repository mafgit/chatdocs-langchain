from ddgs import DDGS

with DDGS() as ddgs:
    results = ddgs.text("Python programming", max_results=5)
    for result in results:
        # 'title'
        # 'href'
        # 'body'
        print(result)