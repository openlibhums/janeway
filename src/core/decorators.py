def has_mat2(original_function):
    """
    A decorator to check mat2 requirements
    @param original_function: the function to decorate
    @return: the original function if mat2 is installed, otherwise None
    """
    def wrapper_function(*arg, **kwargs):
        if check_mat2():
            return original_function(*arg, **kwargs)
        else:
            return None

    return wrapper_function


def check_mat2():
    try:
        import libmat2
        return True
    except:
        return False


def has_pandoc(original_function):
    """
    A decorator to check pandoc requirements
    @param original_function: the function to decorate
    @return: the original function if pandoc is installed, otherwise None
    """
    def wrapper_function(*arg, **kwargs):
        if check_pandoc():
            return original_function(*arg, **kwargs)
        else:
            return None
    return wrapper_function


def check_pandoc():
    try:
        import pypandoc
        return True
    except:
        return False