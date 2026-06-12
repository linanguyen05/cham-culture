import google.generativeai as genai
genai.configure(api_key="AIzaSyC5kMPjvbzw23u9Lf4B5RzBEelLKjQWWcY")

for m in genai.list_models():
    print(m.name)