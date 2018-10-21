def pretty_print_pendulum_duration(duration):
    if duration.days > 0:
        pretty = '{} days, {}:{}:{}'.format(
            duration.days,
            duration.hours,
            duration.minutes,
            duration.remaining_seconds)
    else:
        pretty = '{}:{}:{}'.format(
            duration.hours,
            duration.minutes,
            duration.remaining_seconds)
    return pretty