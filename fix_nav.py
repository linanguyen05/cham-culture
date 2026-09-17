import glob

for file in glob.glob('frontend/**/*.html', recursive=True):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = content.replace('<a href="#">Tìm hiểu</a>', '<a href="/learn.html">Tìm hiểu</a>')
    new_content = new_content.replace('<a href="#">Chatbot</a>', '<a href="/chatbot.html">Chatbot</a>')
    if new_content != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
