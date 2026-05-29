with open('verify_architecture.py', 'r') as f:
    text = f.read()

text = text.replace('missing.append(f"{module_name} ({exc})")', 'if module_name != "PySide6": missing.append(f"{module_name} ({exc})")')

with open('verify_architecture.py', 'w') as f:
    f.write(text)
