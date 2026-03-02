"""Fix nested f-string syntax error in app.py."""

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact problematic section and replace it
# The broken part: f-string with nested f-string and escaped quotes inside st.button
import re

# Pattern to find the problematic st.button call block
pattern = r"        if st\.button\(\s+f\".*?is_selected.*?tmpl.*?name.*?\",\s+key=f\"tmpl_\{tmpl\['id'\]\}\",\s+\):"

def replacement(m):
    return """        btn_label = '✅ 選択中' if is_selected else '選択：' + tmpl['name']
        if st.button(
            btn_label,
            key=f"tmpl_{tmpl['id']}",
        ):"""

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content != content:
    print("Replacement made successfully")
else:
    print("Pattern not matched, trying line-by-line approach")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        raw_line = line.encode('utf-8')
        if b'is_selected' in raw_line and b'tmpl' in raw_line and b'name' in raw_line and b'else' in raw_line and b'st.button' not in raw_line:
            print(f"Found problem line at index {i}: {repr(line[:60])}")
            lines[i] = "        btn_label = '✅ 選択中' if is_selected else '選択：' + tmpl['name']"
            # Next lines should be: key=f"tmpl..." and )
            # Check if the previous line is st.button(
            if i > 0 and 'st.button(' in lines[i-1]:
                lines[i-1] = "        if st.button("
                lines[i] = "            btn_label,"
                print("Fixed button structure")
            new_content = '\n'.join(lines)
            break

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Written.")

# Validate
import ast
try:
    ast.parse(new_content)
    print("AST parse OK!")
except SyntaxError as e:
    print(f"Still has error: {e}")
