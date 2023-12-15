def print_log(output, msg, is_display=True):
    if is_display:
        print('{}'.format(msg))
    output.append('{}'.format(msg))