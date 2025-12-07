import re
import sys

def fix_patch(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        if line.startswith('@@'):
            # Parse header
            match = re.match(r'^@@ -(\d+),(\d+) \+(\d+),(\d+) @@(.*)', line)
            if match:
                old_start = match.group(1)
                # old_len = match.group(2) # We will recalculate this
                new_start = match.group(3)
                # new_len = match.group(4) # We will recalculate this
                suffix = match.group(5)

                # Read hunk content
                hunk_lines = []
                i += 1
                while i < n:
                    next_line = lines[i]
                    if next_line.startswith('diff --git') or next_line.startswith('@@'):
                        break
                    hunk_lines.append(next_line)
                    i += 1
                
                # Calculate lengths
                context_count = 0
                deleted_count = 0
                added_count = 0
                
                for hl in hunk_lines:
                    if hl.startswith(' '):
                        context_count += 1
                    elif hl.startswith('-'):
                        deleted_count += 1
                    elif hl.startswith('+'):
                        added_count += 1
                    elif hl.strip() == '':
                         # Empty line in patch usually treated as context if it doesn't have a marker?
                         # Actually, in a valid patch, empty lines inside hunk should start with space.
                         # But sometimes editors strip trailing whitespace.
                         # If it's truly empty, it might be context.
                         # Let's assume it's context if it's not + or -.
                         context_count += 1
                    elif hl.startswith('\\'):
                        # \ No newline at end of file
                        pass
                    else:
                        # Maybe context line missing space?
                        # Or maybe it's a parsing error.
                        # For now assume context.
                        context_count += 1

                new_old_len = context_count + deleted_count
                new_new_len = context_count + added_count
                
                new_header = f"@@ -{old_start},{new_old_len} +{new_start},{new_new_len} @@{suffix}\n"
                new_lines.append(new_header)
                new_lines.extend(hunk_lines)
                continue
        
        new_lines.append(line)
        i += 1

    with open(filepath, 'w') as f:
        f.writelines(new_lines)

if __name__ == '__main__':
    fix_patch(sys.argv[1])
