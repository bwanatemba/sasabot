class Pagination:
    """
    A pagination utility class that mimics Flask-SQLAlchemy's pagination behavior
    for use with MongoEngine QuerySets.
    """
    
    def __init__(self, page, per_page, total, items):
        self.page = page
        self.per_page = per_page
        self.total = total
        self.items = list(items)
        
    @property
    def pages(self):
        """Total number of pages"""
        return (self.total + self.per_page - 1) // self.per_page
    
    @property
    def has_prev(self):
        """Whether there's a previous page"""
        return self.page > 1
    
    @property
    def has_next(self):
        """Whether there's a next page"""
        return self.page < self.pages
    
    @property
    def prev_num(self):
        """Previous page number"""
        return self.page - 1 if self.has_prev else None
    
    @property
    def next_num(self):
        """Next page number"""
        return self.page + 1 if self.has_next else None
    
    def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
        """
        Iterates over the page numbers in the pagination. This method yields
        page numbers and None values. None values mean that there is a gap
        in the page numbers.
        """
        last = self.pages
        
        for num in range(1, last + 1):
            if num <= left_edge or \
               (self.page - left_current - 1 < num < self.page + right_current) or \
               num > last - right_edge:
                yield num
            else:
                # Check if we need to add a gap
                if num == left_edge + 1 or num == last - right_edge:
                    yield None
