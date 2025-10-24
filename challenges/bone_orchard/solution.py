# take in the number
n = input()

# calculate answer
import sys
from collections import Counter

lines = n.strip().split('\n') if '\n' in n else [n, input()]
N, T = map(int, lines[0].split())
values = list(map(int, lines[1].split()))

# Count frequency of each value
freq = Counter(values)

# Find unique pairs
pairs = []
seen = set()

for val in freq:
    complement = T - val
    if complement in freq:
        if val < complement:
            pairs.append((val, complement))
        elif val == complement and freq[val] >= 2:
            if val not in seen:
                pairs.append((val, val))
                seen.add(val)

# Sort pairs
pairs.sort()

# Format output
K = len(pairs)
if K == 0:
    answer = "0\n"
else:
    pair_strings = [f"({x},{y})" for x, y in pairs]
    answer = f"{K}\n{' '.join(pair_strings)}"

# print answer
print(answer)
