from textblob import TextBlob
import re

score = TextBlob("@json @sgon ").sentiment

print (score)
text = "@snap @snapchat fuck all of yall"

pattern = re.compile(r"\s([@#][\w_-]+)")
new = re.sub(pattern, text, text)

print (new)