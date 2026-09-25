global_var_1 = 10
global_var_2 = "hello"

mylist=globals().items()

for name in mylist:
    print(f"Name: {name}\n")