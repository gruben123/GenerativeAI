def simple_decorator(func):
    def wrapper():
        print("before the greet function call")
        func()  # this is the greet() function call
        print("after the greet function call")

    return wrapper


@simple_decorator
def greet():
    print("hello")


greet()
