from Watch.ai import analyze_answer

q = "Tell me about your personal life"
a = "my self edward im currently purscying BCA at kristu jayanti college"

print("Question:", q)
print("Answer:", a)
print('\n--- AI Feedback ---\n')
print(analyze_answer(q, a))
