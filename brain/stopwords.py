stopfrags=(
    ('limited',),
    ('article',()),
    ('article',(),(),()),
    )


class Stopword():
    def __init__(self):
        #TODO db for stopfrags?
        self.stopFrags = stopfrags

