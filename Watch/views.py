import re
import time

from django.db.models import Avg, Sum
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.utils.html import escape
from django.utils.safestring import mark_safe

from .forms import RegisterForm
from .models import InterviewQuestion, InterviewAttempt
from .ai import analyze_answer


# HOME PAGE

def home(request):
    return render(request, 'home.html')


# LOGIN PAGE

def login_view(request):

    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect('/dashboard')

    return render(request, 'login.html')


# REGISTER PAGE

def register(request):

    form = RegisterForm()

    if request.method == 'POST':

        form = RegisterForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect('/login')

    context = {
        'form': form
    }

    return render(request, 'register.html', context)


# DASHBOARD PAGE

def dashboard(request):
    return render(request, 'dashboard.html')


CATEGORY_MAP = {
    'HR': 'HR',
    'Python': 'Technical',
    'Aptitude': 'Aptitude',
}


def get_category_label(raw_category):
    return CATEGORY_MAP.get(raw_category, raw_category)


def parse_feedback_metrics(feedback):
    communication_score = 0.0
    confidence_score = 0.0
    score = 0.0

    if not feedback:
        return communication_score, confidence_score, score

    comm_match = re.search(r'Communication Rating\s*\(1-10\)\s*[:\-]?\s*(\d+(?:\.\d+)?)', feedback, re.I)
    conf_match = re.search(r'Confidence Rating\s*\(1-10\)\s*[:\-]?\s*(\d+(?:\.\d+)?)', feedback, re.I)
    score_match = re.search(r'Score out of 10\s*[:\-]?\s*(\d+(?:\.\d+)?)', feedback, re.I)

    if comm_match:
        communication_score = float(comm_match.group(1))
    if conf_match:
        confidence_score = float(conf_match.group(1))
    if score_match:
        score = float(score_match.group(1))

    if communication_score == 0 and score > 0:
        communication_score = score
    if confidence_score == 0 and score > 0:
        confidence_score = score

    return communication_score, confidence_score, score


def save_interview_attempt(request, question, answer, feedback, category_label):
    try:
        duration_seconds = 0.0
        start_time = request.session.pop('question_start_time', None)
        if start_time is not None:
            duration_seconds = max(0.0, time.time() - float(start_time))
    except Exception:
        duration_seconds = 0.0

    communication_score, confidence_score, score = parse_feedback_metrics(feedback)

    if request.user.is_authenticated and answer and feedback and not feedback.startswith('Error:'):
        InterviewAttempt.objects.create(
            user=request.user,
            question=question,
            category=category_label,
            answer=answer,
            feedback=feedback,
            score=score,
            communication_score=communication_score,
            confidence_score=confidence_score,
            duration_seconds=duration_seconds,
        )


def performance(request):
    attempts = InterviewAttempt.objects.filter(user=request.user)
    total_interviews = attempts.count()
    avg_score = attempts.aggregate(Avg('score'))['score__avg'] or 0
    total_time_seconds = attempts.aggregate(Sum('duration_seconds'))['duration_seconds__sum'] or 0
    total_time_hours = int(total_time_seconds // 3600)
    total_time_minutes = int((total_time_seconds % 3600) // 60)
    total_time_text = f'{total_time_hours}h {total_time_minutes}m' if total_time_hours else f'{total_time_minutes}m'

    categories = ['HR', 'Technical', 'Aptitude']
    category_stats = {}
    for category in categories:
        cat_attempts = attempts.filter(category=category)
        count = cat_attempts.count()
        category_stats[category] = {
            'count': count,
            'avg_communication': cat_attempts.aggregate(Avg('communication_score'))['communication_score__avg'] or 0,
            'avg_confidence': cat_attempts.aggregate(Avg('confidence_score'))['confidence_score__avg'] or 0,
            'avg_overall': cat_attempts.aggregate(Avg('score'))['score__avg'] or 0,
        }

    context = {
        'total_interviews': total_interviews,
        'average_score': round(avg_score, 1),
        'accuracy': round(avg_score * 10, 0),
        'total_time_text': total_time_text,
        'category_stats': category_stats,
    }
    return render(request, 'performance.html', context)


def restart_performance(request):
    if request.method == 'POST' and request.user.is_authenticated:
        InterviewAttempt.objects.filter(user=request.user).delete()
    return redirect('/performance')


def reports(request):
    attempts = InterviewAttempt.objects.filter(user=request.user).order_by('-created_at')
    counts = {
        'all': attempts.count(),
        'HR': attempts.filter(category='HR').count(),
        'Technical': attempts.filter(category='Technical').count(),
        'Aptitude': attempts.filter(category='Aptitude').count(),
    }
    context = {
        'attempts': attempts,
        'counts': counts,
    }
    return render(request, 'reports.html', context)


def format_feedback_html(feedback):
    if not feedback:
        return ""

    normalized = feedback.replace('\r\n', '\n').replace('\r', '\n').strip()
    section_pattern = re.compile(
        r'(?m)^\s*(\d+)\.\s*(.+?)(?:\n|$)(.*?)(?=(?:^\s*\d+\.\s)|\Z)',
        re.DOTALL
    )
    html_parts = []

    for match in section_pattern.finditer(normalized):
        number = match.group(1)
        raw_title = match.group(2).strip()
        body = match.group(3).strip()

        title = raw_title
        inline_body = ""
        if ':' in raw_title:
            parts = raw_title.split(':', 1)
            title = parts[0].strip()
            inline_body = parts[1].strip()

        if inline_body:
            body = (inline_body + '\n' + body).strip()

        html_parts.append('<div class="feedback-block">')
        html_parts.append(
            f'<div class="feedback-heading">{escape(number)}. {escape(title).upper()}</div>'
        )
        if body:
            escaped_body = escape(body).replace('\n', '<br>')
            html_parts.append(f'<div class="feedback-text">{escaped_body}</div>')
        html_parts.append('</div>')

    if not html_parts:
        html_parts.append(
            f'<div class="feedback-text">{escape(normalized).replace("\n", "<br>")}</div>'
        )

    return ''.join(html_parts)


# INTERVIEW MAIN PAGE

def interview(request):
    return render(request, 'interview.html')

def features(request):
    return render(request, 'features.html')


def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')

def learnmore(request):
    return render(request, 'learnmore.html')


# HR INTERVIEW PAGE

def hr_interview(request, index=0):

    questions = InterviewQuestion.objects.filter(
        category='HR'
    )

    questions = list(questions)

    total_questions = len(questions)

    feedback = ""

    answer = ""

    if total_questions == 0:

        return render(request, 'hr.html', {
            'question': None
        })

    if index >= total_questions:

        return render(request, 'hr.html', {

            'completed': True,

            'total_questions': total_questions

        })

    if index < 0:
        index = 0

    question = questions[index]

    if request.method == 'GET':
        request.session['question_start_time'] = time.time()

    if request.method == 'POST':

        answer = request.POST.get('answer')

        if answer:

            try:

                feedback = analyze_answer(
                    question.question,
                    answer
                )

                save_interview_attempt(
                    request,
                    question,
                    answer,
                    feedback,
                    'HR'
                )

            except Exception as e:

                feedback = f"Error: {e}"

    next_index = index + 1

    previous_index = index - 1

    context = {

        'question': question,

        'next_index': next_index,

        'previous_index': previous_index,

        'current_index': index + 1,

        'total_questions': total_questions,

        'feedback': feedback,

        'feedback_html': mark_safe(format_feedback_html(feedback)),

        'answer': answer

    }

    return render(request, 'hr.html', context)


# TECHNICAL INTERVIEW PAGE

def technical_interview(request, index=0):

    questions = InterviewQuestion.objects.filter(
        category='Python'
    )

    questions = list(questions)

    total_questions = len(questions)

    feedback = ""

    answer = ""

    if total_questions == 0:

        return render(request, 'technical.html', {
            'question': None
        })

    if index >= total_questions:

        return render(request, 'technical.html', {

            'completed': True,

            'total_questions': total_questions

        })

    if index < 0:
        index = 0

    question = questions[index]

    if request.method == 'GET':
        request.session['question_start_time'] = time.time()

    if request.method == 'POST':

        answer = request.POST.get('answer')

        if answer:

            try:

                feedback = analyze_answer(
                    question.question,
                    answer
                )

                save_interview_attempt(
                    request,
                    question,
                    answer,
                    feedback,
                    'Technical'
                )

            except Exception as e:

                feedback = f"Error: {e}"

    next_index = index + 1

    previous_index = index - 1

    context = {

        'question': question,

        'next_index': next_index,

        'previous_index': previous_index,

        'current_index': index + 1,

        'total_questions': total_questions,

        'feedback': feedback,

        'feedback_html': mark_safe(format_feedback_html(feedback)),

        'answer': answer

    }

    return render(request, 'technical.html', context)


# APTITUDE INTERVIEW PAGE

def aptitude_interview(request, index=0):

    questions = InterviewQuestion.objects.filter(
        category='Aptitude'
    )

    questions = list(questions)

    total_questions = len(questions)

    feedback = ""

    answer = ""

    if total_questions == 0:

        return render(request, 'aptitude.html', {
            'question': None
        })

    if index >= total_questions:

        return render(request, 'aptitude.html', {

            'completed': True,

            'total_questions': total_questions

        })

    if index < 0:
        index = 0

    question = questions[index]

    if request.method == 'GET':
        request.session['question_start_time'] = time.time()

    if request.method == 'POST':

        answer = request.POST.get('answer')

        if answer:

            try:

                feedback = analyze_answer(
                    question.question,
                    answer
                )

                save_interview_attempt(
                    request,
                    question,
                    answer,
                    feedback,
                    'Aptitude'
                )

            except Exception as e:

                feedback = f"Error: {e}"

    next_index = index + 1

    previous_index = index - 1

    context = {

        'question': question,

        'next_index': next_index,

        'previous_index': previous_index,

        'current_index': index + 1,

        'total_questions': total_questions,

        'feedback': feedback,

        'feedback_html': mark_safe(format_feedback_html(feedback)),

        'answer': answer

    }

    return render(request, 'aptitude.html', context)