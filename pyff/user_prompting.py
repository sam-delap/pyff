def prompt_for_stat(stat_name: str, stat_dtype: type, current_year: int):
    """Internal function to handle prompting the user to enter projected values"""
    need_answer = True
    stat_value = None
    while need_answer:
        try:
            stat_value = input(f"Estimated {stat_name} for {current_year}: ")
            stat_value = stat_dtype(stat_value)
            need_answer = False
        except ValueError:
            print(f"This is not a valid {stat_dtype}!")
    if stat_value is None:
        raise ValueError(f"Stat value for {stat_name} not captured")
    return stat_value
