import os

target_dir = r'C:\Users\varun\Desktop\rag\ecommerce_support_agent'

for root, _, files in os.walk(target_dir):
    if 'venv' in root or 'chroma_db' in root:
        continue
    for file in files:
        if file.endswith('.md') or file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content.replace('ABC', 'ABC').replace('ABC', 'ABC')
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Updated {filepath}')
