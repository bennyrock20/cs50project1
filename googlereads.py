import requests

res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "TQamOYJgVhdWxbL3lzg","isbns":"9781632168146"})
print(res.json())