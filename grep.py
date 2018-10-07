
import argparse
import sys


def output(line):
    print(line)


def print_with_line_number_and_colon(line_number, line):
    """
    Печатает с номером строки: номер с 1, ex: '1:fggf'
    :param line_number: номер строки
    :param line: строка
    """
    line = str(line_number) + ':' + line
    output(line)


def print_with_line_number_and_dash(line_number, line):
    """
    Печатает с номером строки: номер с 1, ex: '1-fggf'
    :param line_number: номер строки
    :param line: строка
    """
    line = str(line_number) + '-' + line
    output(line)


def print_formatted_output(line, line_index, last_printed_index, buffer_before, params):
    """
    Влияет на отображение результата, просто печатает строчку; если в контексте появляется строка,
    удовлетворяющая условиям задачи, вывод прекращается
    :param line: строка для печати
    :param line_index: номер строки, который печатается если флаг line_number
    :param last_printed_index: номер строки, которая была распечатана последней (для флага line_number)
    :param buffer_before: буфер строк предыдущих
    :param params: аргументы командной строки
    """
    # context = params.context if params.context else params.before_context
    if params.context or params.before_context:
        # Печать N строчек до текущей
        for i in buffer_before:
            if i['index'] == -1:  # buffer_before не полон
                continue
            if i['index'] > last_printed_index:
                if params.line_number:
                    print_with_line_number_and_dash(i['index'] + 1, i['line'])
                else:
                    output(i['line'])

    if params.line_number:
        print_with_line_number_and_colon(line_index + 1, line)
    else:
        output(line)


def check_pattern_in_line(pattern_for_compare, line_for_compare):
    """
    Проверяет есть ли паттерн в строке по правилам регулярного выражения (?, *)
    :param pattern_for_compare: str паттерн для сравнения
    :param line_for_compare: str строка, в которой ведется поиск
    :return: bool есть или нет
    """
    # бьем подстроку на части, так как звездочка - последовательность любой длины
    pattern_elements = [s for s in pattern_for_compare.split('*') if s]
    begin = 0  # индекс, начиная с которого ведем поиск части подстроки
    for s in pattern_elements:
        search_started_at = 0  # индекс, начиная с которого ведем поиск части подстроки для текущей итерации
        found = False  # часть подстроки найдена
        if begin >= len(line_for_compare):  # поиск окончен, но s еще есть
            return False
        # перебираем посимвольный поиск для части подстроки
        while search_started_at < len(line_for_compare):
            # начинаем поиск с индекса подряд
            current_search_index = search_started_at
            for index, symbol in enumerate(s):
                if current_search_index >= len(line_for_compare):
                    # вышли за границу поиска => часть подстроки не найдена
                    break
                if symbol == '?':
                    if index == len(s) - 1:  # '?' в маске - последний символ
                        found = True
                        break
                    current_search_index += 1
                    continue  # к следующему символу
                if symbol != line_for_compare[current_search_index]:
                    # символ не совпадает, поиск ведем заново со след. символа
                    break
                else:
                    # совпал
                    if index == len(s) - 1:  # это был последний символ из подстроки
                        found = True
                        break
                    current_search_index += 1  # к следующему символу в части подстроки
            if found:  # часть подстроки найдена
                break
            # ведем поиск части подстроки со следующего символа
            search_started_at += 1
        if not found:  # в конечном итоге, часть подстроки не найдена
            return False
        # часть подстроки найдена, переходим к следующей части
        begin = search_started_at + len(s) + 1

    return True


def check_line_satisfies_condition(pattern_for_compare, line_for_compare, params):
    """
    Проверяет ли подходит строка паттерну при условии invert или без invert
    :param pattern_for_compare: паттерн
    :param line_for_compare: строка из текста
    :param params: параметры КС, достаем invert
    :return: удовлетворяет условию грепа или нет: bool
    """
    if params.invert:
        if not check_pattern_in_line(pattern_for_compare, line_for_compare):
            return True
    else:
        if check_pattern_in_line(pattern_for_compare, line_for_compare):
            return True

    return False


def append_line(buffer, index, element):
    buffer = buffer[1:]
    buffer.append({'index': index, 'line': element})

    return buffer


def grep(lines, params):
    pattern = params.pattern
    count = 0
    last_printed_index = -1

    count_before_context = params.context if params.context else params.before_context
    count_after_context = params.context if params.context else params.after_context
    buffer_before = [{'index': -1, 'line': ''} for _ in range(count_before_context)]
    current_count_after = 0  # сколько еще строк выводить после

    for line_index, line in enumerate(lines):
        line = line.rstrip()
        pattern_for_compare = pattern  # меняется, если есть _ignore_case_
        line_for_compare = line  # меняется, если есть _ignore_case_

        # Проверяем флаги, которые влияют на сравнение шаблона и строки
        if params.ignore_case:
            pattern_for_compare = pattern.lower()
            line_for_compare = line.lower()

        # выводим строки после
        if count_after_context and current_count_after > 0:
            if not check_line_satisfies_condition(
                    pattern_for_compare,
                    line_for_compare,
                    params):
                if params.line_number:
                    print_with_line_number_and_dash(line_index + 1, line)
                else:
                    output(line)
                current_count_after -= 1
                last_printed_index = line_index

        # основная строка, удовлетворяющая условию
        if check_line_satisfies_condition(pattern_for_compare, line_for_compare, params):
            if not params.count:
                print_formatted_output(
                    line, line_index, last_printed_index, buffer_before, params)
                last_printed_index = line_index
                current_count_after = count_after_context
            count += 1

        # добавляем в буфер
        if count_before_context:
            buffer_before = append_line(buffer_before, line_index, line)

    if params.count:
        output(str(count))


def parse_args(args):
    parser = argparse.ArgumentParser(description='This is a simple grep on python')
    parser.add_argument(
        '-v', action="store_true", dest="invert", default=False, help='Selected lines are those not matching pattern.')
    parser.add_argument(
        '-i', action="store_true", dest="ignore_case", default=False, help='Perform case insensitive matching.')
    parser.add_argument(
        '-c',
        action="store_true",
        dest="count",
        default=False,
        help='Only a count of selected lines is written to standard output.')
    parser.add_argument(
        '-n',
        action="store_true",
        dest="line_number",
        default=False,
        help='Each output line is preceded by its relative line number in the file, starting at line 1.')
    parser.add_argument(
        '-C',
        action="store",
        dest="context",
        type=int,
        default=0,
        help='Print num lines of leading and trailing context surrounding each match.')
    parser.add_argument(
        '-B',
        action="store",
        dest="before_context",
        type=int,
        default=0,
        help='Print num lines of trailing context after each match')
    parser.add_argument(
        '-A',
        action="store",
        dest="after_context",
        type=int,
        default=0,
        help='Print num lines of leading context before each match.')
    parser.add_argument('pattern', action="store", help='Search pattern. Can contain magic symbols: ?*')
    return parser.parse_args(args)


def main():
    params = parse_args(sys.argv[1:])
    grep(sys.stdin.readlines(), params)


if __name__ == '__main__':
    main()