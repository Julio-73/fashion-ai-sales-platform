import sys
import os

test_dir = r'C:\Users\User\Documents\ai-sales-agent-saas\backend\tests\unit'

files_to_fix = [
    'test_customer_service.py',
    'test_schemas.py',
    'test_auth_service.py',
    'test_product_service.py',
    'test_conversation_service.py',
]

for fname in files_to_fix:
    fpath = os.path.join(test_dir, fname)
    if not os.path.exists(fpath):
        print(f'Skipping {fname} - not found')
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Replace the problematic escaped triple quotes at file start
    if content.startswith('\\"\\"\\"'):
        content = content[3:]  # Remove the leading \"
        if content.startswith('\\'):
            content = content[1:]  # Remove the second \ if present
        if content.startswith('"') or content.startswith('\\'):
            content = content[1:]  # Remove the third
        content = '"""' + content
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Fixed {fname}')
print('Done')
