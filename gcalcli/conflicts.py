
class ShowConflicts:
    active_events = []

    def __init__(self, show):
        if show:
            self.show = show
        else:
            self.show = self._default_show

    def show_conflicts(self, latest_event):
        """Events must be passed in chronological order"""
        start = latest_event['s']
        for event in self.active_events:
            if (event['e'] > start):
                self.show(event)
        self.active_events = list(
            filter(lambda e: e['e'] > start, self.active_events))
        self.active_events.append(latest_event)

    def _default_show(self, e):
        print(e)
