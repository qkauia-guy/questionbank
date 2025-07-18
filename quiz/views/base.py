import random
from opencc import OpenCC


cc = OpenCC("s2t")


def convert_to_traditional(text):
    return cc.convert(text)


def check_answer(question, selected_answer, fill_input):
    correct_answer = question.answer.upper()
    if question.is_fill_in:
        return fill_input.strip() == question.fill_answer.strip()
    else:
        user_ans = "".join(selected_answer).strip().upper()
        return (
            user_ans == correct_answer
            if question.require_order
            else sorted(user_ans) == sorted(correct_answer)
        )


def shuffle_choice_values(question):
    if question.is_fill_in:
        return {}, ""

    answer_letters = question.answer.strip().upper().replace(",", "")
    choices = {
        "A": question.choice_a,
        "B": question.choice_b,
        "C": question.choice_c,
        "D": question.choice_d,
        "E": question.choice_e,
        "F": question.choice_f,
        "G": question.choice_g,
        "H": question.choice_h,
    }
    valid_choices = {k: v for k, v in choices.items() if v and v.strip().upper() != "X"}

    items = list(valid_choices.items())
    random.shuffle(items)

    shuffled, old_to_new = {}, {}
    for idx, (old_letter, content) in enumerate(items):
        new_letter = chr(ord("A") + idx)
        shuffled[new_letter] = content
        old_to_new[old_letter] = new_letter

    new_answer = "".join([old_to_new[l] for l in answer_letters if l in old_to_new])
    return shuffled, new_answer


def sort_key(val):
    try:
        cleaned = val.replace(" ", "")
        if "-" in cleaned:
            parts = cleaned.split("-")
            return (int(parts[0]), int(parts[1]))
        return (int(cleaned), 0)
    except:
        return (float("inf"), float("inf"))


def generate_options_text(question):
    text = ""
    for letter in "ABCDEFGH":
        choice = getattr(question, f"choice_{letter.lower()}", "").strip()
        if choice and choice.upper() != "X":
            text += f"{letter}. {choice}\n"
    return text
