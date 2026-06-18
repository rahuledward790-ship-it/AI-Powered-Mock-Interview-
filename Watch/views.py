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
    from .models import Resume
    resume = None
    if request.user.is_authenticated:
        resume = Resume.objects.filter(user=request.user).first()
    return render(request, 'dashboard.html', {'resume': resume})


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


def save_aptitude_attempt(request, question, answer, feedback):
    try:
        duration_seconds = 0.0
        start_time = request.session.get('question_start_time')
        if start_time is not None:
            duration_seconds = max(0.0, time.time() - float(start_time))
    except Exception:
        duration_seconds = 0.0

    communication_score, confidence_score, score = parse_feedback_metrics(feedback)
    is_correct = score >= 7.0
    marks_scored = 10 if is_correct else 0
    percentage = (score / 10.0) * 100.0
    final_result = 'Pass' if is_correct else 'Fail'

    if request.user.is_authenticated and answer and feedback and not feedback.startswith('Error:'):
        from .models import AptitudeAttempt
        AptitudeAttempt.objects.create(
            user=request.user,
            question=question,
            answer=answer,
            score=marks_scored,
            percentage=percentage,
            time_taken=int(duration_seconds),
            is_correct=is_correct,
            final_result=final_result,
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
    questions = InterviewQuestion.objects.filter(category='HR')
    questions = list(questions)
    total_questions = len(questions)
    feedback = ""
    answer = ""

    if total_questions == 0:
        return render(request, 'hr.html', {'question': None})

    if index == 0:
        request.session['hr_start_time'] = time.time()

    start_time = request.session.get('hr_start_time')
    if start_time is None:
        request.session['hr_start_time'] = time.time()
        start_time = request.session['hr_start_time']

    remaining_seconds = 300 - int(time.time() - start_time)
    if remaining_seconds <= 0:
        return render(request, 'hr.html', {
            'completed': True,
            'time_over': True,
            'total_questions': total_questions
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
                feedback = analyze_answer(question.question, answer)
                save_interview_attempt(request, question, answer, feedback, 'HR')
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
        'answer': answer,
        'remaining_seconds': max(0, remaining_seconds),
    }

    return render(request, 'hr.html', context)


# TECHNICAL INTERVIEW PAGE

def technical_interview(request, index=0):
    questions = InterviewQuestion.objects.filter(category='Python')
    questions = list(questions)
    total_questions = len(questions)
    feedback = ""
    answer = ""

    if total_questions == 0:
        return render(request, 'technical.html', {'question': None})

    if index == 0:
        request.session['technical_start_time'] = time.time()

    start_time = request.session.get('technical_start_time')
    if start_time is None:
        request.session['technical_start_time'] = time.time()
        start_time = request.session['technical_start_time']

    remaining_seconds = 600 - int(time.time() - start_time)
    if remaining_seconds <= 0:
        return render(request, 'technical.html', {
            'completed': True,
            'time_over': True,
            'total_questions': total_questions
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
                feedback = analyze_answer(question.question, answer)
                save_interview_attempt(request, question, answer, feedback, 'Technical')
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
        'answer': answer,
        'remaining_seconds': max(0, remaining_seconds),
    }

    return render(request, 'technical.html', context)


# APTITUDE INTERVIEW PAGE

def aptitude_interview(request, index=0):
    questions = InterviewQuestion.objects.filter(category='Aptitude')
    questions = list(questions)
    total_questions = len(questions)
    feedback = ""
    answer = ""

    if total_questions == 0:
        return render(request, 'aptitude.html', {'question': None})

    if index == 0:
        request.session['aptitude_start_time'] = time.time()

    start_time = request.session.get('aptitude_start_time')
    if start_time is None:
        request.session['aptitude_start_time'] = time.time()
        start_time = request.session['aptitude_start_time']

    remaining_seconds = 600 - int(time.time() - start_time)
    if remaining_seconds <= 0:
        return render(request, 'aptitude.html', {
            'completed': True,
            'time_over': True,
            'total_questions': total_questions
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
                feedback = analyze_answer(question.question, answer)
                save_interview_attempt(request, question, answer, feedback, 'Aptitude')
                save_aptitude_attempt(request, question, answer, feedback)
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
        'answer': answer,
        'remaining_seconds': max(0, remaining_seconds),
    }

    return render(request, 'aptitude.html', context)


# RESUME UPLOAD VIEW
def upload_resume(request):
    if request.method == 'POST' and request.user.is_authenticated:
        phone_number = request.POST.get('phone_number', '')
        resume_file = request.FILES.get('resume')
        if resume_file:
            from .models import Resume
            # Remove previous resumes for this user
            Resume.objects.filter(user=request.user).delete()
            Resume.objects.create(
                user=request.user,
                phone_number=phone_number,
                resume_file=resume_file
            )
    return redirect('/dashboard')


# AJAX SAVE ATTEMPT VIEW
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def save_attempt(request):
    import json
    from django.http import JsonResponse
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            question_text = data.get('question', '')
            answer_text = data.get('answer', '')
            category = data.get('category', 'General')
            
            overall_score = float(data.get('overall', 0))
            communication_score = float(data.get('communication', 0))
            confidence_score = float(data.get('confidence', 0))
            body_language_score = float(data.get('body_language', 0))
            eye_contact_score = float(data.get('eye_contact', 0))
            fluency_score = float(data.get('fluency', 0))
            grammar_analysis = data.get('grammar_analysis', '')
            duration = float(data.get('duration', 0))
            feedback = data.get('feedback', '')
            
            from .models import InterviewQuestion, InterviewAttempt
            q, created = InterviewQuestion.objects.get_or_create(
                question=question_text,
                defaults={'category': category, 'difficulty': 'Intermediate'}
            )
            
            InterviewAttempt.objects.create(
                user=request.user,
                question=q,
                category=category,
                answer=answer_text,
                feedback=feedback,
                score=overall_score,
                communication_score=communication_score,
                confidence_score=confidence_score,
                body_language_score=body_language_score,
                eye_contact_score=eye_contact_score,
                fluency_score=fluency_score,
                grammar_analysis=grammar_analysis,
                duration_seconds=duration
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'unauthorized'}, status=401)


# CUSTOM ADMIN LOGIN AND DASHBOARD
def admin_login(request):
    error = ""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username == 'admin' and password == 'admin123':
            from django.contrib.auth.models import User
            user, created = User.objects.get_or_create(
                username='admin',
                defaults={'is_superuser': True, 'is_staff': True}
            )
            if created or not user.check_password('admin123'):
                user.set_password('admin123')
                user.save()
            
            user = authenticate(request, username='admin', password='admin123')
            if user is not None:
                login(request, user)
                return redirect('/admin-dashboard/')
        else:
            error = "Invalid admin credentials!"
            
    return render(request, 'admin_login.html', {'error': error})


def admin_dashboard(request):
    if not request.user.is_authenticated or request.user.username != 'admin':
        return redirect('/admin-dashboard/login/')
        
    from .models import Resume, InterviewAttempt, AptitudeAttempt
    
    resumes = Resume.objects.select_related('user').all()
    candidates_list = []
    for resume in resumes:
        latest_attempt = InterviewAttempt.objects.filter(user=resume.user).order_by('-created_at').first()
        aptitude_attempt = AptitudeAttempt.objects.filter(user=resume.user).order_by('-created_at').first()
        interview_date = None
        if latest_attempt and aptitude_attempt:
            interview_date = max(latest_attempt.created_at, aptitude_attempt.created_at)
        elif latest_attempt:
            interview_date = latest_attempt.created_at
        elif aptitude_attempt:
            interview_date = aptitude_attempt.created_at
            
        candidates_list.append({
            'resume': resume,
            'user': resume.user,
            'phone_number': resume.phone_number,
            'interview_date': interview_date,
            'hiring_status': resume.hiring_status,
        })
        
    interviews = InterviewAttempt.objects.select_related('user', 'question').all().order_by('-created_at')
    aptitudes = AptitudeAttempt.objects.select_related('user', 'question').all().order_by('-created_at')
    
    context = {
        'candidates': candidates_list,
        'interviews': interviews,
        'aptitudes': aptitudes,
    }
    return render(request, 'admin_dashboard.html', context)


def admin_hire_candidate(request, resume_id):
    if not request.user.is_authenticated or request.user.username != 'admin':
        return redirect('/admin-dashboard/login/')
        
    from .models import Resume
    try:
        resume = Resume.objects.get(id=resume_id)
        if resume.hiring_status == 'Selected':
            resume.hiring_status = 'Pending'
        else:
            resume.hiring_status = 'Selected'
        resume.save()
    except Resume.DoesNotExist:
        pass
        
    return redirect('/admin-dashboard/')