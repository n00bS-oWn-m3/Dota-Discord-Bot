# All helper-commands related to converting things

# convert the time in seconds to a nice string (up to hours)
def timer_converter(seconds: int):
    seconds = abs(seconds)
    if seconds == 0:
        return "the start of the game"
    times = [
        ["{t} second{s}", 60],
        ["{t} minute{s}", 60],
        ["{t} hour{s}", 24]
    ]
    result = []
    divisor = 1
    for time in times:
        t = int((seconds // divisor) % time[1])
        if t > 0:
            result.insert(0, time[0].format(t=t, s="s" if t > 1 else ""))
        divisor *= time[1]


    result_list = [f"{result[0]}", f"{result[0]} and {result[1]}", f"{result[0]}, {result[1]} and {result[2]}"]
    return result_list[len(result) - 1]