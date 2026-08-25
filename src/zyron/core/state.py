class ZyronState:
    def __init__(self):
        self._active = False

    def turn_on(self):
        self._active = True

    def turn_off(self):
        self._active = False

    def is_active(self):
        return self._active
