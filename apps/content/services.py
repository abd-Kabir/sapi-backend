def calculate_correct_answers(answer_options, post_answers_list):
    total_answers = len(post_answers_list)

    correct_answers = {}
    for answer_option in answer_options:
        count = post_answers_list.count(answer_option)
        percent = round(count / total_answers * 100, 2) if total_answers > 0 else 0
        correct_answers[answer_option] = {
            'answers_count': count,
            'percent': percent
        }

    return correct_answers
