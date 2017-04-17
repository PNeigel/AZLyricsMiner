import matplotlib.pyplot as plt
import numpy as np
import re
from nltk.tag import pos_tag

# Visualize the wordcount of Ed Sheeran Lyrics
# We use nltk to get only nouns

# Open file with all words
f = open("ED_SHEERAN_all.txt", "rb")
all_words = f.readline()
f.close()

# Split the single string into multiple strings, because
# the module re can't handle too many words
single_words = all_words.split()

# 'Clean up' the words from &'s, -'s etc.
for i, word in enumerate(single_words):
    single_words[i] = re.sub(r"\W", "", word)

# Create one string again to feed to nltk's pos_tag
one = ""
for word in single_words:
    one += word
    one += " "

# Create the list of tagged words
tagged_words = pos_tag(one.split())

# Filter proper nouns, proper nouns, plurals
nouns = [word for word,pos in tagged_words if pos in ['NNP', 'NN', 'NNS']]

# Get count of words (histogram)
words, counts = np.unique(nouns, return_counts=True)
args = np.argsort(counts)[::-1]

# Plot 20 most common words
fig, ax = plt.subplots(1, figsize=(15,5))
ax.plot(counts[args][:20])
ax.set_xticks(np.arange(20))
ax.set_xticklabels(words[args][:20])
plt.title("Wordcount Ed Sheeran Lyrics", size=20)
plt.xlabel("Word", size=15)
plt.ylabel("Count", size=15)
plt.savefig("Wordcount_ed_sheeran.png")