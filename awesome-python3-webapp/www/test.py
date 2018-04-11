class Test(object):
    # def __init__(self, name):
    #     self.name = name
    def run(self):
        print("runing...")

    @property
    def age(self):
        return self._age
    @age.setter
    def age(self,vale):
        if vale > 100:
            self._age = 100
        else:
            self._age = vale

class TestMore:
    def run(self):
        print("run")
test = Test()
test.age = 123
print(test.age)
