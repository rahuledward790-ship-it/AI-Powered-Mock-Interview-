#!/usr/bin/env python
"""
Test script to verify FREE AI feedback system is working
Run this to test before deploying!
"""

import os
import sys
import django

# Use UTF-8 output when possible to avoid Windows console encoding errors.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    pass

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project24.settings')
django.setup()

from Watch.ai import analyze_answer

print("\n" + "="*60)
print("🤖 AI INTERVIEW FEEDBACK SYSTEM - TEST")
print("="*60)

# Sample test data
test_cases = [
    {
        "category": "HR",
        "question": "Tell me about yourself",
        "answer": "I am a software developer with 5 years experience. I worked on various projects using Python and JavaScript."
    },
    {
        "category": "Technical",
        "question": "What is the difference between list and tuple in Python?",
        "answer": "Lists are mutable and tuples are immutable"
    },
    {
        "category": "Aptitude",
        "question": "If a train travels 300 miles in 5 hours, what is its average speed?",
        "answer": "The speed is 60 miles per hour"
    }
]

print("\n📝 Testing with sample answers...\n")

for i, test in enumerate(test_cases, 1):
    print(f"\n{'─'*60}")
    print(f"Test {i}: {test['category']}")
    print(f"{'─'*60}")
    print(f"❓ Question: {test['question']}")
    print(f"📝 Answer: {test['answer']}")
    print(f"\n⏳ Getting AI feedback (this may take a moment)...\n")
    
    try:
        feedback = analyze_answer(test['question'], test['answer'])
        print(f"✅ FEEDBACK:\n")
        print(feedback)
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*60)
print("✅ Test Complete!")
print("="*60)
print("\n📋 Next Steps:")
print("   1. If you see feedback above, your AI system is working! 🎉")
print("   2. If you see an error, follow the SETUP_FREE_AI.md guide")
print("   3. Run 'python manage.py runserver' to start Django")
print("   4. Test in your web interface!\n")
