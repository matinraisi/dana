import json
from django.db import transaction
from ..models import Question, Choice, ExamAttempt, StudentAnswer, MatchingPair, FillBlankAnswer, OrderingItem

QUESTION_TYPE_MULTIPLE_CHOICE = 'multiple_choice'
QUESTION_TYPE_MULTIPLE_ANSWER = 'multiple_answer'
QUESTION_TYPE_TRUE_FALSE = 'true_false'
QUESTION_TYPE_SHORT_ANSWER = 'short_answer'
QUESTION_TYPE_ESSAY = 'essay'
QUESTION_TYPE_MATCHING = 'matching'
QUESTION_TYPE_FILL_BLANK = 'fill_blank'
QUESTION_TYPE_ORDERING = 'ordering'


def calculate_question_score(question, answer):
    qtype = question.question_type
    points = question.points

    if qtype == QUESTION_TYPE_MULTIPLE_CHOICE:
        selected = answer.selected_choices.all()
        correct = question.choices.filter(is_correct=True)
        if selected.count() == 1 and correct.count() == 1 and selected.first() == correct.first():
            return points
        return 0.0

    elif qtype == QUESTION_TYPE_TRUE_FALSE:
        selected = answer.selected_choices.all()
        correct = question.choices.filter(is_correct=True)
        if selected.count() == 1 and correct.count() == 1 and selected.first() == correct.first():
            return points
        return 0.0

    elif qtype == QUESTION_TYPE_MULTIPLE_ANSWER:
        selected = set(answer.selected_choices.all())
        correct = set(question.choices.filter(is_correct=True))
        if selected == correct:
            return points
        if not selected:
            return 0.0
        score_per_choice = points / len(correct) if correct else 0
        positive = sum(score_per_choice for c in selected if c.is_correct)
        negative = sum(score_per_choice for c in selected if not c.is_correct)
        return max(0, positive - negative)

    elif qtype in (QUESTION_TYPE_SHORT_ANSWER, QUESTION_TYPE_FILL_BLANK):
        if not answer.text_answer:
            return 0.0
        user_text = answer.text_answer.strip().lower()
        correct_answers = question.fill_blank_answers.all()
        if not correct_answers.exists():
            return 0.0
        for ca in correct_answers:
            acceptable = [ca.answer_text.strip().lower()]
            if ca.acceptable_alternatives:
                acceptable.extend(
                    [a.strip().lower() for a in ca.acceptable_alternatives.split('\n') if a.strip()]
                )
            if user_text in acceptable:
                return points
        return 0.0

    elif qtype == QUESTION_TYPE_MATCHING:
        if not answer.matching_answers:
            return 0.0
        pairs = question.matching_pairs.all()
        try:
            user_map = json.loads(answer.matching_answers) if isinstance(answer.matching_answers, str) else answer.matching_answers
        except (json.JSONDecodeError, TypeError):
            return 0.0
        correct_count = 0
        for pair in pairs:
            # بررسی آیا کاربر pair.id رو به مقدار صحیح نسبت داده
            if str(pair.id) in user_map:
                user_value = str(user_map[str(pair.id)])
                # مقدار صحیح: pair.id (یعنی هر آیتم به خودش نسبت داده شده)
                if user_value == str(pair.id):
                    correct_count += 1
        if correct_count == pairs.count():
            return points
        return round(points * correct_count / pairs.count(), 1) if pairs.count() else 0

    elif qtype == QUESTION_TYPE_ORDERING:
        if not answer.ordering_answers:
            return 0.0
        items = question.ordering_items.all()
        try:
            user_order = json.loads(answer.ordering_answers) if isinstance(answer.ordering_answers, str) else answer.ordering_answers
        except (json.JSONDecodeError, TypeError):
            return 0.0
        correct_positions = {str(it.id): it.correct_order for it in items}
        correct_count = 0
        for idx, item_id in enumerate(user_order):
            if str(item_id) in correct_positions and correct_positions[str(item_id)] == idx + 1:
                correct_count += 1
        if correct_count == len(items):
            return points
        return round(points * correct_count / len(items), 1) if items else 0

    elif qtype == QUESTION_TYPE_ESSAY:
        return None

    return 0.0


def auto_grade_attempt(attempt):
    answers = attempt.answers.all()
    total_score = 0.0
    max_score = 0.0
    all_graded = True

    for answer in answers:
        question = answer.question
        max_score += question.points

        if question.question_type == QUESTION_TYPE_ESSAY:
            if answer.score is None:
                all_graded = False
                continue
            total_score += answer.score
        else:
            score = calculate_question_score(question, answer)
            answer.score = score
            answer.is_correct = (score == question.points) if question.points > 0 else False
            answer.save()
            total_score += score

    attempt.max_score = int(max_score)
    if all_graded:
        attempt.score = total_score
        attempt.status = 'graded'
        attempt.is_passed = total_score >= attempt.exam.pass_score
    else:
        attempt.score = total_score
        if attempt.answers.exclude(question__question_type=QUESTION_TYPE_ESSAY).count() == attempt.answers.count():
            attempt.status = 'graded'
            attempt.is_passed = total_score >= attempt.exam.pass_score
        else:
            attempt.status = 'submitted'
    attempt.save()
    return attempt


def create_attempt(exam, student, request=None):
    from django.utils import timezone
    existing = ExamAttempt.objects.filter(exam=exam, student=student)
    attempt_number = existing.count() + 1

    if exam.attempts_allowed > 0 and existing.filter(status__in=('submitted', 'graded')).count() >= exam.attempts_allowed:
        raise ValueError("تعداد دفعات مجاز تلاش برای این آزمون به پایان رسیده است.")

    attempt = ExamAttempt.objects.create(
        exam=exam,
        student=student,
        attempt_number=attempt_number,
        max_score=exam.total_score,
        start_time=timezone.now(),
        ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR') if request else None,
        user_agent=getattr(request, 'META', {}).get('HTTP_USER_AGENT', '')[:500] if request else '',
    )

    questions = list(exam.questions.all())
    if exam.shuffle_questions:
        import random
        random.shuffle(questions)
    if exam.random_question_count:
        import random
        questions = random.sample(questions, min(exam.random_question_count, len(questions)))

    for q in questions:
        StudentAnswer.objects.create(attempt=attempt, question=q)

    return attempt


def submit_attempt(attempt, form_data, request=None):
    from django.utils import timezone
    from django.db import transaction

    # بررسی وضعیت آزمون
    if attempt.status != 'in_progress':
        return attempt

    # بررسی زمان باقی‌مانده
    if attempt.is_time_up:
        attempt.end_time = timezone.now()
        attempt.status = 'submitted'
        attempt.save()
        auto_grade_attempt(attempt)
        return attempt

    with transaction.atomic():
        for answer in attempt.answers.all():
            q = answer.question
            prefix = f'q_{q.id}'

            if q.question_type in ('multiple_choice', 'true_false'):
                choice_id = form_data.get(prefix)
                if choice_id:
                    try:
                        choice = Choice.objects.get(id=choice_id, question=q)
                        answer.selected_choices.add(choice)
                    except Choice.DoesNotExist:
                        pass

            elif q.question_type == 'multiple_answer':
                choice_ids = form_data.getlist(prefix)
                for cid in choice_ids:
                    try:
                        choice = Choice.objects.get(id=cid, question=q)
                        answer.selected_choices.add(choice)
                    except Choice.DoesNotExist:
                        pass

            elif q.question_type == 'short_answer':
                answer.text_answer = form_data.get(prefix, '')

            elif q.question_type == 'essay':
                answer.text_answer = form_data.get(prefix, '')
                if f'{prefix}_file' in (request.FILES if request else {}):
                    answer.file_answer = request.FILES[f'{prefix}_file']

            elif q.question_type == 'matching':
                matching_data = {}
                for key, val in form_data.items():
                    if key.startswith(f'{prefix}_'):
                        left_id = key.replace(f'{prefix}_', '')
                        matching_data[left_id] = val
                answer.matching_answers = json.dumps(matching_data, ensure_ascii=False)

            elif q.question_type == 'fill_blank':
                answer.text_answer = form_data.get(prefix, '')

            elif q.question_type == 'ordering':
                order_data = form_data.getlist(prefix)
                answer.ordering_answers = json.dumps(order_data, ensure_ascii=False)

            answer.save()

        attempt.end_time = timezone.now()
        attempt.save()

    return auto_grade_attempt(attempt)
